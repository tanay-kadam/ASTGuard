from __future__ import annotations


class RelationProjector:
    def project(
        self, lexical_edges: list[tuple[int, int]], leaf_to_bpe: dict[int, list[int]],
        *, symmetric: bool = False,
    ) -> tuple[list[tuple[int, int]], list[dict]]:
        projected: set[tuple[int, int]] = set()
        groups: list[dict] = []
        for left, right in sorted(set(lexical_edges)):
            pairs = {(i, j) for i in leaf_to_bpe.get(left, []) for j in leaf_to_bpe.get(right, []) if i != j}
            if symmetric:
                pairs |= {(j, i) for i, j in pairs}
            projected |= pairs
            groups.append({"lexical_edge": [left, right], "projected_pairs": [list(x) for x in sorted(pairs)]})
        return sorted(projected), groups

