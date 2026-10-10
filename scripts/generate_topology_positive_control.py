"""Generate a paired, leakage-resistant topology-token positive control.

Every token sequence occurs with both labels.  Labels differ only in whether AST
edges connect equal token types (positive) or different token types (negative).
All eligible nodes have one incoming and one outgoing edge in both conditions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


MANIFEST_HASH = "725e6dc910b29f6771435f28865c8692f9bf35dfa421318741ccf2820f5c02c8"
PREPROCESSING_HASH = "9846b0032e74b70b976ab1d361064ce8c1888b5b952b4f5adc693d5789803adc"
TOKEN_TYPES = (100, 200, 300, 400)
TOKENS_PER_TYPE = 6
CLS_ID = 0
SEP_ID = 2


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            for row in rows:
                stream.write(json.dumps(row, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _cycle(nodes: list[int]) -> list[list[int]]:
    return [[nodes[index], nodes[(index + 1) % len(nodes)]] for index in range(len(nodes))]


def _edges(tokens: list[int], label: int, rng: random.Random) -> list[list[int]]:
    positions: dict[int, list[int]] = defaultdict(list)
    for index, token in enumerate(tokens, start=1):
        positions[token].append(index)
    for token in TOKEN_TYPES:
        rng.shuffle(positions[token])
    if label == 1:
        return sorted(edge for token in TOKEN_TYPES for edge in _cycle(positions[token]))
    edges: list[list[int]] = []
    for left_type, right_type in ((TOKEN_TYPES[0], TOKEN_TYPES[1]), (TOKEN_TYPES[2], TOKEN_TYPES[3])):
        # Two alternating six-node cycles preserve the same unlabeled topology
        # as the two within-type cycles used by the corresponding positive pair.
        # Only the alignment between endpoints and token types changes.
        for offset in (0, TOKENS_PER_TYPE // 2):
            left = positions[left_type][offset:offset + TOKENS_PER_TYPE // 2]
            right = positions[right_type][offset:offset + TOKENS_PER_TYPE // 2]
            alternating = [node for pair in zip(left, right) for node in pair]
            edges.extend(_cycle(alternating))
    return sorted(edges)


def _row(role: str, pair_index: int, label: int, tokens: list[int], rng: random.Random) -> dict:
    input_ids = [CLS_ID, *tokens, SEP_ID]
    pair_id = f"pc-{role}-{pair_index:06d}"
    return {
        "sample_id": f"{pair_id}-y{label}",
        "component_id": pair_id,
        "dataset": "topology_positive_control",
        "role": role,
        "split_hash": MANIFEST_HASH,
        "preprocessing_hash": PREPROCESSING_HASH,
        "label": label,
        "input_ids": input_ids,
        "attention_mask": [True] * len(input_ids),
        "special_tokens_mask": [True] + [False] * len(tokens) + [True],
        "ast_token_edges": _edges(tokens, label, rng),
        "dfg_token_edges": [],
        "source_sha256": hashlib.sha256(bytes(str(input_ids), "utf-8")).hexdigest(),
    }


def generate_split(role: str, pairs: int, rng: random.Random, seen: set[tuple[int, ...]]) -> list[dict]:
    rows = []
    for pair_index in range(pairs):
        while True:
            tokens = [token for token in TOKEN_TYPES for _ in range(TOKENS_PER_TYPE)]
            rng.shuffle(tokens)
            key = tuple(tokens)
            if key not in seen:
                seen.add(key)
                break
        rows.extend((_row(role, pair_index, 0, tokens, rng), _row(role, pair_index, 1, tokens, rng)))
    return rows


def validate_rows(train: list[dict], tune: list[dict]) -> None:
    by_component: dict[str, list[dict]] = defaultdict(list)
    for row in [*train, *tune]:
        by_component[row["component_id"]].append(row)
        eligible = range(1, len(row["input_ids"]) - 1)
        incoming = Counter(right for _, right in row["ast_token_edges"])
        outgoing = Counter(left for left, _ in row["ast_token_edges"])
        if any(incoming[index] != 1 or outgoing[index] != 1 for index in eligible):
            raise AssertionError("every eligible node must have one incoming and one outgoing AST edge")
        if row["dfg_token_edges"]:
            raise AssertionError("DFG must be empty")
        token_by_position = dict(enumerate(row["input_ids"]))
        same_type = [token_by_position[left] == token_by_position[right]
                     for left, right in row["ast_token_edges"]]
        if not same_type or any(value != bool(row["label"]) for value in same_type):
            raise AssertionError("edge/token alignment does not encode the requested label")
    for pair in by_component.values():
        if len(pair) != 2 or {row["label"] for row in pair} != {0, 1}:
            raise AssertionError("each component must contain an opposite-label pair")
        if pair[0]["input_ids"] != pair[1]["input_ids"]:
            raise AssertionError("paired labels must have identical sequence inputs")
    train_components = {row["component_id"] for row in train}
    tune_components = {row["component_id"] for row in tune}
    if train_components & tune_components:
        raise AssertionError("train/tune components overlap")
    train_sequences = {tuple(row["input_ids"]) for row in train}
    tune_sequences = {tuple(row["input_ids"]) for row in tune}
    if train_sequences & tune_sequences:
        raise AssertionError("train/tune token sequences overlap")
    for role, rows in (("train", train), ("tune", tune)):
        if sum(row["label"] for row in rows) * 2 != len(rows):
            raise AssertionError(f"{role} is not balanced")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("data/positive_control/v1"))
    parser.add_argument("--train-pairs", type=int, default=2048)
    parser.add_argument("--tune-pairs", type=int, default=512)
    parser.add_argument("--seed", type=int, default=20261006)
    args = parser.parse_args(argv)
    if args.train_pairs <= 0 or args.tune_pairs <= 0:
        raise ValueError("pair counts must be positive")
    train_path = args.output_root / "train.jsonl"
    tune_path = args.output_root / "tune.jsonl"
    manifest_path = args.output_root / "manifest.json"
    if any(path.exists() for path in (train_path, tune_path, manifest_path)):
        raise FileExistsError("positive-control outputs already exist; use a new output root")
    rng = random.Random(args.seed)
    seen: set[tuple[int, ...]] = set()
    train = generate_split("train", args.train_pairs, rng, seen)
    tune = generate_split("tune", args.tune_pairs, rng, seen)
    validate_rows(train, tune)
    _atomic_jsonl(train_path, train)
    _atomic_jsonl(tune_path, tune)
    manifest = {
        "kind": "paired_topology_token_positive_control_v1",
        "official_test_used": False,
        "generation_seed": args.seed,
        "manifest_hash": MANIFEST_HASH,
        "preprocessing_hash": PREPROCESSING_HASH,
        "train_pairs": args.train_pairs,
        "train_rows": len(train),
        "tune_pairs": args.tune_pairs,
        "tune_rows": len(tune),
        "sequence_length": 2 + len(TOKEN_TYPES) * TOKENS_PER_TYPE,
        "token_types": list(TOKEN_TYPES),
        "tokens_per_type": TOKENS_PER_TYPE,
        "train_sha256": _sha256(train_path),
        "tune_sha256": _sha256(tune_path),
    }
    _atomic_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
