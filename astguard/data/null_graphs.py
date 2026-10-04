from __future__ import annotations

from collections import Counter, defaultdict
import random

from astguard.utils.hashing import sha256_text


def _token_edges(row: dict, relation: str) -> list[tuple[int, int]]:
    field = f"{relation}_token_edges"
    if field in row:
        return sorted({tuple(edge) for edge in row.get(field, []) if edge[0] != edge[1]})
    pairs = set()
    for group in row.get("edge_projection_groups", []):
        if group.get("relation") == relation:
            pairs.update(tuple(edge) for edge in group.get("projected_pairs", []) if edge[0] != edge[1])
    return sorted(pairs)


def _position_blocks(row: dict, blocks: int) -> dict[int, int]:
    eligible = [index for index, (visible, special) in enumerate(
        zip(row["attention_mask"], row["special_tokens_mask"])) if visible and not special]
    return {index: min(blocks - 1, blocks * rank // max(1, len(eligible)))
            for rank, index in enumerate(eligible)}


def _permute_relation(row: dict, relation: str, *, seed: int, draw: int,
                      position_blocks: int) -> tuple[list[list[int]], dict]:
    edges = set(_token_edges(row, relation))
    block_of = _position_blocks(row, position_blocks)
    incoming = Counter(right for left, right in edges)
    outgoing = Counter(left for left, right in edges)
    groups: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for node in block_of:
        groups[(incoming[node], outgoing[node], block_of[node])].append(node)
    seed_text = f"matched-null-v1|{seed}|{draw}|{row['sample_id']}|{relation}|{position_blocks}"
    rng = random.Random(int(sha256_text(seed_text)[:16], 16))
    permutation = {}
    for key in sorted(groups):
        members = sorted(groups[key])
        shuffled = members[:]
        rng.shuffle(shuffled)
        permutation.update(zip(members, shuffled))
    changed = {(permutation[left], permutation[right]) for left, right in edges}
    if Counter(right for left, right in changed) != incoming:
        raise AssertionError("matched null changed per-token incoming degrees")
    if Counter(left for left, right in changed) != outgoing:
        raise AssertionError("matched null changed per-token outgoing degrees")
    original_block_pairs = Counter((block_of[left], block_of[right]) for left, right in edges)
    changed_block_pairs = Counter((block_of[left], block_of[right]) for left, right in changed)
    if changed_block_pairs != original_block_pairs:
        raise AssertionError("matched null changed position-block edge counts")
    fraction = len(edges - changed) / len(edges) if edges else 0.0
    return [list(edge) for edge in sorted(changed)], {
        "relation": relation,
        "edges": len(edges),
        "movable_tokens": sum(len(group) for (incoming_degree,outgoing_degree,_),group in groups.items()
                              if len(group) > 1 and incoming_degree + outgoing_degree > 0),
        "changed_fraction": fraction,
    }


def matched_null_graph(row: dict, *, seed: int, draw: int,
                       position_blocks: int = 4) -> tuple[dict, list[dict]]:
    """Permute equal-degree tokens within position blocks to create a matched null.

    The null preserves every token's incoming/outgoing degree and the number of
    edges between position blocks. It changes only endpoint identity; tokens,
    labels, sequence length, relation counts, and special-token exclusions remain.
    """
    if position_blocks <= 0:
        raise ValueError("position_blocks must be positive")
    graph = {}
    diagnostics = []
    for relation in ("ast", "dfg"):
        graph[f"{relation}_token_edges"], detail = _permute_relation(
            row, relation, seed=seed, draw=draw, position_blocks=position_blocks)
        diagnostics.append(detail)
    return graph, diagnostics


class MatchedNullGraphDataset:
    """Dataset view that retains real edges and attaches deterministic null graphs."""

    def __init__(self, base, *, seed: int, samples: int = 4, position_blocks: int = 4,
                 namespace: str = "train"):
        if samples <= 0:
            raise ValueError("at least one null graph sample is required")
        self.base = base
        self.seed = int(sha256_text(f"matched-null-dataset-v1|{seed}|{namespace}")[:16], 16)
        self.samples = samples
        self.position_blocks = position_blocks
        self.stats = {
            "kind": "degree_position_matched_token_nulls",
            "examples": len(base),
            "samples_per_example": samples,
            "position_blocks": position_blocks,
            "namespace": namespace,
        }

    def __len__(self):
        return len(self.base)

    def __getitem__(self, index):
        source = self.base[index]
        row = dict(source)
        graphs, diagnostics = [], []
        for draw in range(self.samples):
            graph, detail = matched_null_graph(
                source, seed=self.seed, draw=draw, position_blocks=self.position_blocks)
            graphs.append(graph)
            diagnostics.append(detail)
        row["null_graphs"] = graphs
        row["null_graph_diagnostics"] = diagnostics
        return row
