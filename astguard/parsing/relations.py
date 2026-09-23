from __future__ import annotations

from collections import deque

from .trees import ParsedTree


class SyntaxRelationBuilder:
    def __init__(self, radius: int = 4):
        self.radius = radius

    def build(self, tree: ParsedTree) -> tuple[list[int], list[tuple[int, int]]]:
        if not tree.successful:
            return [], []
        leaves = [node.id for node in tree.nodes if not node.children and node.kind != "comment"]
        adjacency: dict[int, set[int]] = {node.id: set() for node in tree.nodes}
        for node in tree.nodes:
            for child in node.children:
                adjacency[node.id].add(child)
                adjacency[child].add(node.id)
        leaf_index = {node_id: index for index, node_id in enumerate(leaves)}
        edges: set[tuple[int, int]] = set()
        leaf_nodes = set(leaves)
        for leaf in leaves:
            queue = deque([(leaf, 0)])
            visited = {leaf}
            while queue:
                current, distance = queue.popleft()
                if distance == self.radius:
                    continue
                for neighbor in adjacency[current]:
                    if neighbor in visited:
                        continue
                    visited.add(neighbor)
                    next_distance = distance + 1
                    if neighbor in leaf_nodes and neighbor != leaf:
                        a, b = leaf_index[leaf], leaf_index[neighbor]
                        edges.add((min(a, b), max(a, b)))
                    queue.append((neighbor, next_distance))
        return leaves, sorted(edges)

    def anchored_parent_child(self,tree):
        leaves=[node.id for node in tree.nodes if not node.children and node.kind!='comment']
        indices={node:i for i,node in enumerate(leaves)}
        anchors={node:node for node in leaves}
        for node in reversed(tree.nodes):
            descendants=[anchors[c] for c in node.children if c in anchors]
            if descendants:anchors[node.id]=descendants[0]
        edges=set()
        for node in tree.nodes:
            for child in node.children:
                if node.id in anchors and child in anchors and anchors[node.id]!=anchors[child]:
                    edges.add(tuple(sorted((indices[anchors[node.id]],indices[anchors[child]]))))
        return leaves,sorted(edges)
