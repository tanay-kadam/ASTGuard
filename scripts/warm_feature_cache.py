"""Fill the shared feature cache for every registry cohort/variant with a process pool.

prepare_feature_registry.py reads features only through FeatureCache.get_or_build,
so once this pass completes the registry build is a sequential cache read. The
cache key (source hash, preprocessing hash, sample id) is independent of which
process built an entry, so warming cannot change any registered feature.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.utils.atomic_io import atomic_write_json

_STATE = {}


def _init(checkpoint, cache_root, variants):
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    from astguard.alignment.tokenizer import CanonicalTokenizer
    from astguard.data.cache import FeatureCache
    from astguard.data.preprocess import _preprocessing_hash
    tokenizer = CanonicalTokenizer(checkpoint)
    caches = []
    for fields in variants:
        digest = _preprocessing_hash(tokenizer.identity_hash, fields["max_length"], False, fields["ast_relation"],
                                     fields["dfg_symmetry"], fields["structural_context"], fields["topology"],
                                     fields["annotation_masking"])
        caches.append(FeatureCache(Path(cache_root) / digest, digest))
    _STATE.update(tokenizer=tokenizer, caches=caches, variants=variants)


def _build(task):
    from astguard.data.preprocess import preprocess_record
    from astguard.data.schema import SampleRecord
    index, row = task
    record = SampleRecord.from_dict(row)
    fields, cache = _STATE["variants"][index], _STATE["caches"][index]
    started = time.perf_counter()
    try:
        cache.get_or_build(record.raw_sha256, lambda: dataclasses.asdict(
            preprocess_record(record, _STATE["tokenizer"], **fields)), sample_id=record.sample_id)
        failure = None
    except Exception as exc:
        failure = {"sample_id": record.sample_id, "variant": index, "exception": type(exc).__name__, "reason": str(exc)}
    return failure, record.sample_id, index, time.perf_counter() - started


def _tasks(by_records, variant_indices):
    from astguard.data.schema import read_jsonl
    for records, wanted in by_records.items():
        for path in records:
            for row in read_jsonl(path):
                if row["sample_id"] in wanted:
                    yield from ((index, row) for index in variant_indices)


def main(argv=None) -> int:
    from scripts.prepare_feature_registry import DEFAULT_VARIANTS
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--variants", default="all", help="comma-separated DEFAULT_VARIANTS indices, or 'all'")
    parser.add_argument("--views", default="all")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 4))
    parser.add_argument("--progress-every", type=int, default=2000)
    parser.add_argument("--report", default="artifacts/release_gates/cache_warm_report.json")
    args = parser.parse_args(argv)

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    variants = [{"annotation_masking": "a_priori_v1", **fields} for fields in (plan.get("variants") or DEFAULT_VARIANTS)]
    indices = list(range(len(variants))) if args.variants == "all" else [int(v) for v in args.variants.split(",")]
    views = sorted(plan["cohorts"]) if args.views == "all" else args.views.split(",")
    by_records = {}
    for view in views:
        cohort = plan["cohorts"][view]
        manifest = json.loads(Path(cohort["manifest"]).read_text(encoding="utf-8"))
        key = tuple(cohort["records"])
        by_records.setdefault(key, set()).update(manifest["ordered_sample_ids"])

    started, done, failures, slowest = time.time(), 0, [], []
    total = sum(len(ids) for ids in by_records.values()) * len(indices)
    with Pool(args.workers, initializer=_init, initargs=(plan["checkpoint"], plan.get("cache_root", "data/cache/features"),
                                                          variants)) as pool:
        for failure, sample_id, index, seconds in pool.imap_unordered(_build, _tasks(by_records, indices), chunksize=2):
            done += 1
            if failure:
                failures.append(failure)
            slowest = sorted([*slowest, (seconds, sample_id, index)], reverse=True)[:25]
            if done % args.progress_every == 0 or done == total:
                elapsed = time.time() - started
                print(f"WARM {done}/{total} failures={len(failures)} elapsed={elapsed:.0f}s "
                      f"eta={elapsed / done * (total - done):.0f}s", flush=True)
    report = {"status": "complete" if not failures else "complete_with_failures", "plan": args.plan,
              "views": views, "variants": [variants[i] for i in indices], "tasks": done,
              "failures": failures, "elapsed_seconds": round(time.time() - started, 1),
              "slowest_tasks": [{"seconds": round(s, 2), "sample_id": i, "variant": v} for s, i, v in slowest]}
    atomic_write_json(args.report, report)
    print(f"WARM_DONE tasks={done} failures={len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
