from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass(frozen=True)
class TreeNode:
    id: int
    kind: str
    start_byte: int
    end_byte: int
    parent: int | None
    children: tuple[int, ...]
    named: bool


@dataclasses.dataclass(frozen=True)
class ParsedTree:
    language: str
    nodes: tuple[TreeNode, ...]
    root: int
    error_count: int
    missing_count: int
    covered_bytes: int
    native_root: Any = dataclasses.field(default=None, repr=False, compare=False)

    @property
    def successful(self) -> bool:
        return self.error_count == 0 and self.missing_count == 0


def _language(name: str):
    try:
        from tree_sitter import Language, Parser  # type: ignore
        module = __import__(f"tree_sitter_{name}")
    except ImportError as exc:
        raise RuntimeError("Tree-sitter C/C++ packages are required for scientific preprocessing") from exc
    return Language(module.language()), Parser


def parse_tree(source: str, language: str) -> ParsedTree:
    lang, Parser = _language(language)
    parser = Parser(lang)
    raw = parser.parse(source.encode("utf-8"))
    nodes: list[TreeNode] = []

    def visit(node: Any, parent: int | None) -> int:
        node_id = len(nodes)
        nodes.append(TreeNode(node_id, node.type, node.start_byte, node.end_byte, parent, (), node.is_named))
        children = tuple(visit(child, node_id) for child in node.children)
        nodes[node_id] = dataclasses.replace(nodes[node_id], children=children)
        return node_id

    root = visit(raw.root_node, None)
    errors = sum(node.kind == "ERROR" for node in nodes)
    def missing_nodes(node):
        return int(node.is_missing) + sum(missing_nodes(child) for child in node.children)
    missing = missing_nodes(raw.root_node)
    covered = raw.root_node.end_byte - raw.root_node.start_byte
    return ParsedTree(language, tuple(nodes), root, errors, missing, covered, raw.root_node)


def select_c_or_cpp(source: str, hint: str | None = None) -> ParsedTree:
    order = ["cpp", "c"] if hint and "++" in hint else ["c", "cpp"]
    candidates = [parse_tree(source, name) for name in order]
    return min(candidates, key=lambda tree: (tree.error_count + tree.missing_count, -tree.covered_bytes, 0 if tree.language == "c" else 1))


def error_free_prefix_forest(tree: ParsedTree,boundary: int) -> ParsedTree:
    """Keep maximal error-free subtrees; disconnected roots cannot create edges."""
    nodes=[]
    def copy(node,parent=None):
        index=len(nodes)
        nodes.append(TreeNode(index,node.type,node.start_byte,node.end_byte,parent,(),node.is_named))
        children=tuple(copy(child,index) for child in node.children if child.end_byte<=boundary)
        nodes[index]=dataclasses.replace(nodes[index],children=children)
        return index
    def visit(node):
        if not node.has_error and not node.is_missing and node.end_byte<=boundary:
            copy(node)
        else:
            for child in node.children:visit(child)
    visit(tree.native_root)
    return ParsedTree(tree.language,tuple(nodes),0,0,0,boundary,tree.native_root)
