"""Prepare or summarize the blinded E12 qualitative error-review artifact."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.analysis.errors import ERROR_CATEGORIES
from astguard.analysis.runner import read_rows
from astguard.data.schema import write_jsonl
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import hash_uniform, sha256_file


def prepare(args):
    sequence = {row["sample_id"]: row for row in read_rows(args.sequence_predictions)}
    adaptive = {row["sample_id"]: row for row in read_rows(args.adaptive_predictions)}
    if set(sequence) != set(adaptive):
        raise ValueError("sequence/adaptive prediction populations differ")
    records = {row["sample_id"]: row for row in read_rows(args.records)}
    features = {row["sample_id"]: row for row in read_rows(args.features)}
    cells = {(left, right): [] for left in (False, True) for right in (False, True)}
    for sample_id in sequence:
        left, right = sequence[sample_id], adaptive[sample_id]
        if int(left["label"]) != int(right["label"]): raise ValueError("label mismatch")
        label = bool(left["label"])
        left_correct = bool(left.get("decisions", {}).get("max_f1")) == label
        right_correct = bool(right.get("decisions", {}).get("max_f1")) == label
        cells[(left_correct, right_correct)].append(sample_id)
    selected = []
    for cell, sample_ids in cells.items():
        ordered = sorted(sample_ids, key=lambda value: hash_uniform(f"e12-cell-v1-{cell}", value))
        for sample_id in ordered[:args.per_cell]:
            record, feature = records[sample_id], features[sample_id]
            selected.append({"review_type": "correctness_cell", "cell": {"sequence_correct": cell[0], "adaptive_correct": cell[1]},
                "sample_id": sample_id, "source": record["source_canonical"], "benchmark_label": record["label"],
                "sequence_decision": sequence[sample_id]["decisions"]["max_f1"],
                "adaptive_decision": adaptive[sample_id]["decisions"]["max_f1"],
                "sequence_score": sequence[sample_id]["probability"], "adaptive_score": adaptive[sample_id]["probability"],
                "parse_status": feature.get("parse_status"), "ast_status": feature.get("ast_status"),
                "dfg_status": feature.get("dfg_status"), "truncated": feature.get("original_bpe_length", 0) > 510,
                "review": {"status": "unreviewed", "reviewer_ids": [], "categories": [],
                           "label_disputed": None, "notes": ""}})
    if args.pairs:
        pair_defs = sorted(read_rows(args.pairs), key=lambda row: hash_uniform("e12-pairs-v1", row["pair_id"]))[:args.pair_count]
        for pair in pair_defs:
            vulnerable, patched = pair["vulnerable_id"], pair["patched_id"]
            if vulnerable not in sequence or patched not in sequence: continue
            selected.append({"review_type": "pair", "pair_id": pair["pair_id"],
                "vulnerable_id": vulnerable, "patched_id": patched,
                "vulnerable_source": records[vulnerable]["source_canonical"],
                "patched_source": records[patched]["source_canonical"],
                "sequence_scores": [sequence[vulnerable]["probability"], sequence[patched]["probability"]],
                "adaptive_scores": [adaptive[vulnerable]["probability"], adaptive[patched]["probability"]],
                "review": {"status": "unreviewed", "reviewer_ids": [], "categories": [],
                           "label_disputed": None, "notes": ""}})
    write_jsonl(args.output, selected)
    return {"status": "prepared_not_reviewed", "rows": len(selected),
            "correctness_cell_counts": {str(key): min(len(value), args.per_cell) for key,value in cells.items()},
            "sequence_predictions_sha256": sha256_file(args.sequence_predictions),
            "adaptive_predictions_sha256": sha256_file(args.adaptive_predictions),
            "output_sha256": sha256_file(args.output)}


def summarize(args):
    rows = read_rows(args.input)
    category_counts = Counter(); reviewers = set(); incomplete = 0; disputed = 0
    for row in rows:
        review = row.get("review", {})
        if review.get("status") != "complete": incomplete += 1; continue
        categories = review.get("categories", [])
        unknown = set(categories) - set(ERROR_CATEGORIES)
        if unknown: raise ValueError(f"unknown annotation categories: {sorted(unknown)}")
        category_counts.update(categories); reviewers.update(review.get("reviewer_ids", []))
        disputed += bool(review.get("label_disputed"))
    result = {"status": "complete" if not incomplete else "incomplete", "row_count": len(rows),
              "reviewed_count": len(rows)-incomplete, "incomplete_count": incomplete,
              "reviewer_count": len(reviewers), "two_reviewer_preference_met": len(reviewers) >= 2,
              "label_disputed_count": disputed, "category_counts": dict(category_counts),
              "input_sha256": sha256_file(args.input)}
    atomic_write_json(args.output, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("prepare"); make.add_argument("--sequence-predictions", required=True)
    make.add_argument("--adaptive-predictions", required=True); make.add_argument("--records", required=True)
    make.add_argument("--features", required=True); make.add_argument("--pairs")
    make.add_argument("--per-cell", type=int, default=20); make.add_argument("--pair-count", type=int, default=20)
    make.add_argument("--output", required=True)
    score = sub.add_parser("summarize"); score.add_argument("--input", required=True); score.add_argument("--output", required=True)
    args = parser.parse_args(argv); result = prepare(args) if args.command == "prepare" else summarize(args)
    if args.command == "prepare": atomic_write_json(Path(args.output).with_suffix(".manifest.json"), result)
    print(json.dumps(result, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
