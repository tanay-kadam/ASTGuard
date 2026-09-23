"""Materialize the train-only rows needed by the manual-edge and overfit release gates.

Both gates select rows from the P_clean train role in a fixed hash order, so
preprocessing only that ordered prefix yields exactly the rows a full-cohort
run would select. Features use the registered primary preprocessing and the
shared feature cache, so later full-cohort preprocessing reuses them.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.alignment.tokenizer import CanonicalTokenizer
from astguard.data.cache import FeatureCache
from astguard.data.preprocess import _preprocessing_hash, preprocess_record
from astguard.data.schema import SampleRecord, read_jsonl, write_jsonl
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import hash_uniform, sha256_file

REVIEW_SALT = "manual-extraction-audit-v1"
OVERFIT_SALT = "baseline-overfit-v1"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", default="data/interim/primevul/records.jsonl")
    parser.add_argument("--manifest", default="artifacts/audits/P_clean.json")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--cache-root", default="data/cache/features")
    parser.add_argument("--review-count", type=int, default=50)
    parser.add_argument("--overfit-per-label", type=int, default=16)
    parser.add_argument("--output-dir", default="data/processed/release_subsets")
    args = parser.parse_args(argv)

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    assignments = {sample: (role, component) for sample, role, component in
                   zip(manifest["ordered_sample_ids"], manifest["roles"], manifest["component_ids"])}
    train = {row["sample_id"]: row for row in read_jsonl(args.records)
             if assignments.get(row["sample_id"], ("",))[0] == "train"}
    tokenizer = CanonicalTokenizer(args.checkpoint)
    preprocessing_hash = _preprocessing_hash(tokenizer.identity_hash, 512, False, "leaf_path_radius4", False,
                                             "full_function", "clean", "a_priori_v1")
    cache = FeatureCache(Path(args.cache_root) / preprocessing_hash, preprocessing_hash)

    def feature(sample_id):
        record = SampleRecord.from_dict(train[sample_id])
        return cache.get_or_build(record.raw_sha256, lambda: dataclasses.asdict(preprocess_record(record, tokenizer)),
                                  sample_id=sample_id)

    def joined(value):
        row = train[value["sample_id"]]
        if value["source_sha256"] != row["raw_sha256"]:
            raise ValueError(f"feature/source hash mismatch: {value['sample_id']}")
        role, component = assignments[value["sample_id"]]
        return value | {"label": row["label"], "role": role, "component_id": component,
                        "split_hash": manifest["file_hash"]}

    target_each = args.review_count // 2
    review, languages, scanned = [], Counter(), 0
    for sample_id in sorted(train, key=lambda s: hash_uniform(REVIEW_SALT, s)):
        if all(languages[lang] >= target_each for lang in ("c", "cpp")):
            break
        scanned += 1
        value = feature(sample_id)
        language = value["language_selected"]
        if value["dfg_status"] != "ok" or language not in {"c", "cpp"} or languages[language] >= target_each:
            continue
        languages[language] += 1
        review.append(value)

    overfit = []
    for label in (0, 1):
        ids = sorted((s for s, row in train.items() if int(row["label"]) == label),
                     key=lambda s: hash_uniform(OVERFIT_SALT, s))[:args.overfit_per_label]
        overfit.extend(joined(feature(s)) for s in ids)

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "review_features.jsonl", review)
    write_jsonl(output / "overfit_train.jsonl", overfit)
    report = {"status": "prepared", "preprocessing_hash": preprocessing_hash, "annotation_masking": "a_priori_v1",
              "manifest": args.manifest, "manifest_file_hash": manifest["file_hash"],
              "records_sha256": sha256_file(args.records),
              "review": {"salt": REVIEW_SALT, "scanned_prefix": scanned, "selected": len(review),
                         "language_counts": dict(languages),
                         "sha256": sha256_file(output / "review_features.jsonl")},
              "overfit": {"salt": OVERFIT_SALT, "per_label": args.overfit_per_label, "rows": len(overfit),
                          "positives": sum(int(r["label"]) for r in overfit),
                          "sha256": sha256_file(output / "overfit_train.jsonl")}}
    atomic_write_json(output / "subset_manifest.json", report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
