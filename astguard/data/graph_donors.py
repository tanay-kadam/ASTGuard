from __future__ import annotations

import random

from astguard.utils.hashing import sha256_text

_EDGE_FIELDS = ("edge_projection_groups", "ast_token_edges", "dfg_token_edges")


def length_matched_donors(lengths: list[int], seed: int) -> tuple[list[int], dict]:
    """Assign every index a donor index with the same token length (no fixed points).

    Indices are bucketed by exact length; a length with a single example is merged
    with the following lengths until the bucket has at least two members (the last
    undersized bucket joins its predecessor). Within each bucket a Sattolo cycle gives
    a derangement, so every example receives another example's graph.
    """
    by_length: dict[int, list[int]] = {}
    for index, length in enumerate(lengths):
        by_length.setdefault(length, []).append(index)
    buckets: list[list[int]] = []
    pending: list[int] = []
    for length in sorted(by_length):
        pending.extend(by_length[length])
        if len(pending) >= 2:
            buckets.append(pending)
            pending = []
    if pending:
        if not buckets:
            raise ValueError("length-matched graph donors require at least two examples")
        buckets[-1].extend(pending)
    rng = random.Random(int(sha256_text(f"graph-donors-v1|{seed}")[:16], 16))
    donors = [-1] * len(lengths)
    for bucket in buckets:
        members = sorted(bucket)
        order = members[:]
        for i in range(len(order) - 1, 0, -1):
            j = rng.randrange(i)
            order[i], order[j] = order[j], order[i]
        for recipient, donor in zip(members, order):
            donors[recipient] = donor
    exact = sum(lengths[i] == lengths[d] for i, d in enumerate(donors))
    stats = {"examples": len(lengths), "buckets": len(buckets), "exact_length_matches": exact,
             "exact_length_fraction": exact / len(lengths) if lengths else 0.0,
             "donors_sha256": sha256_text(",".join(map(str, donors)))}
    return donors, stats


def _valid(pair, special) -> bool:
    left, right = pair
    return left < len(special) and right < len(special) and not special[left] and not special[right]


def transplant_graph(recipient: dict, donor: dict) -> dict:
    """Return the recipient row carrying the donor's structural edges.

    Edges that would land on a recipient special token or beyond its length are
    dropped; with exact-length donors this never happens.
    """
    special = recipient["special_tokens_mask"]
    row = dict(recipient)
    if "edge_projection_groups" in donor:
        row["edge_projection_groups"] = [
            {**group, "projected_pairs": [pair for pair in group["projected_pairs"] if _valid(pair, special)]}
            for group in donor["edge_projection_groups"]]
    for field in ("ast_token_edges", "dfg_token_edges"):
        if field in donor:
            row[field] = [pair for pair in donor[field] if _valid(pair, special)]
    for field in _EDGE_FIELDS:
        if field not in donor:
            row.pop(field, None)
    return row


class GraphDonorDataset:
    """Training view in which each example's graph comes from a fixed length-matched donor."""

    def __init__(self, base, lengths: list[int], seed: int):
        if len(lengths) != len(base):
            raise ValueError("one length per training example is required")
        self.base = base
        self.donors, self.stats = length_matched_donors(lengths, seed)

    def __len__(self):
        return len(self.base)

    def __getitem__(self, index):
        return transplant_graph(self.base[index], self.base[self.donors[index]])
