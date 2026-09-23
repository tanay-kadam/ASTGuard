from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from astguard.analysis.aggregate import ResultAggregator
from astguard.analysis.gates import summarize_gates
from astguard.analysis.plots import write_metric_svg
from astguard.baselines.simple import HashedLogisticBaseline
from astguard.data.adapters import JsonlFunctionAdapter
from astguard.data.audit import LeakageAuditor
from astguard.data.preprocess import preprocess_record
from astguard.data.schema import write_jsonl
from astguard.data.splits import SplitBuilder
from astguard.alignment.tokenizer import SmokeTokenizer
from astguard.evaluation.metrics import evaluate_scores
from astguard.evaluation.thresholds import ThresholdSelector
from astguard.utils.atomic_io import atomic_write_json, atomic_write_text
from astguard.utils.hashing import object_hash, sha256_file
from astguard.utils.provenance import environment_snapshot, source_identity


def fixture_rows() -> list[dict]:
    rows = []
    splits = ["train"] * 36 + ["valid"] * 24
    for index, split in enumerate(splits):
        vulnerable = index % 3 == 0
        body = "char b[8]; strcpy(b, input); return b[0];" if vulnerable else "if (n < 8) { b[n] = 0; } return n;"
        rows.append({"id": f"smoke-{index:03d}", "split": split, "label": int(vulnerable),
                     "source": f"int smoke_{index}(char *input, int n) {{ {body} }}",
                     "repository_url": f"https://example.invalid/project-{index % 7}", "commit_id": f"c{index:04d}"})
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Dependency-free plumbing-only end-to-end smoke test")
    parser.add_argument("--output-root", default="runs")
    args = parser.parse_args(argv)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = Path(args.output_root) / f"smoke-{stamp}-{object_hash(fixture_rows())[:8]}"
    suffix = 0
    while run_root.exists():
        suffix += 1
        run_root = Path(args.output_root) / f"smoke-{stamp}-{object_hash(fixture_rows())[:8]}-{suffix}"
    run_root.mkdir(parents=True)
    raw = run_root / "raw.jsonl"
    with raw.open("w", encoding="utf-8", newline="\n") as handle:
        for row in fixture_rows():
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    records, quarantine = JsonlFunctionAdapter("smoke").read(raw, "synthetic-v1")
    mapping, evidence = LeakageAuditor().build_components(records)
    for record in records:
        record.component_id = mapping[record.sample_id]
    manifest = SplitBuilder().freeze(records, mapping, evidence, view="P_clean", version="smoke-v1")
    by_id = {record.sample_id: record for record in records}
    roles = dict(zip(manifest.ordered_sample_ids, manifest.roles))
    if {r for r in roles.values()} != {"train", "tune", "cal"}:
        raise RuntimeError("smoke fixture failed to produce all local development roles")
    tokenizer = SmokeTokenizer()
    features = {record.sample_id: preprocess_record(record, tokenizer, max_length=64, smoke=True) for record in records}
    write_jsonl(run_root / "records.jsonl", records)
    write_jsonl(run_root / "features.jsonl", features.values())
    atomic_write_json(run_root / "split_manifest.json", dataclasses.asdict(manifest))
    atomic_write_json(run_root / "quarantine.json", quarantine)

    def joined(role):
        result = []
        for sample_id, assigned in roles.items():
            if assigned != role:
                continue
            record, feature = by_id[sample_id], features[sample_id]
            result.append({"sample_id": sample_id, "source_canonical": record.source_canonical, "label": record.label,
                           "ast_token_edges": feature.ast_token_edges, "dfg_token_edges": feature.dfg_token_edges})
        return result

    train, tune, calibration = joined("train"), joined("tune"), joined("cal")
    predictions_files = []
    statuses = []
    for model_id, structural, adaptive in (("sequence_only", False, False), ("ast_dfg_fixed", True, False), ("astguard", True, True)):
        model_dir = run_root / model_id
        model_dir.mkdir()
        model = HashedLogisticBaseline(seed=42, include_structure=structural, adaptive=adaptive)
        history = model.fit(train, epochs=8)
        model.save(model_dir / "checkpoint.json")
        restored = HashedLogisticBaseline.load(model_dir / "checkpoint.json")
        if restored.weights != model.weights:
            raise AssertionError("checkpoint round trip failed")
        cal_scores = [1 / (1 + math.exp(-restored.predict_logit(row))) for row in calibration]
        thresholds = ThresholdSelector().fit(
            [row["sample_id"] for row in calibration], [row["label"] for row in calibration], cal_scores,
            role="cal", checkpoint_hash=sha256_file(model_dir / "checkpoint.json"),
        )
        # Smoke has no official test access; tune is reused only as a plumbing evaluation split and labeled accordingly.
        rows = []
        threshold = float(thresholds["max_f1"].threshold)
        checkpoint_hash = sha256_file(model_dir / "checkpoint.json")
        for row in tune:
            logit = restored.predict_logit(row)
            probability = 1 / (1 + math.exp(-logit))
            rows.append({"run_id": run_root.name, "sample_id": row["sample_id"], "model_id": model_id,
                         "seed": 42, "logit": logit, "probability": probability, "label": row["label"],
                         "dataset":"smoke","view":"smoke_local","split_hash":manifest.file_hash,
                         "config_hash":object_hash({"model_id":model_id,"kind":"plumbing_only"}),
                         "checkpoint_hash":checkpoint_hash,"feature_hash":object_hash({"tokenizer":"smoke"}),
                         "metric_version":"1.0","role": "smoke_evaluation_not_official_test",
                         "threshold_ids":{"max_f1":thresholds["max_f1"].threshold_id},
                         "decisions":{"max_f1":probability >= threshold}})
        prediction_path = model_dir / "predictions.json"
        atomic_write_json(prediction_path, rows)
        predictions_files.append(prediction_path)
        metrics = evaluate_scores([row["label"] for row in rows], [row["probability"] for row in rows], threshold)
        atomic_write_json(model_dir / "metrics.json", metrics)
        atomic_write_json(model_dir / "thresholds.json", {name: dataclasses.asdict(value) for name, value in thresholds.items()})
        atomic_write_json(model_dir / "train_history.json", history)
        statuses.append({"model_id": model_id, "status": "complete", "scientific_status": "plumbing_only"})

    aggregator = ResultAggregator()
    aggregate = aggregator.aggregate_predictions(predictions_files, run_root / "aggregate.json")
    aggregator.build_markdown_table(aggregate, run_root / "smoke_table.md")
    write_metric_svg(aggregate, run_root / "smoke_figure.svg")
    gates = summarize_gates([.5] * sum(len(f.ast_token_edges) > 0 for f in features.values()), [1] * sum(len(f.ast_token_edges) > 0 for f in features.values()))
    atomic_write_json(run_root / "gate_summary.json", gates)
    provenance = {"kind": "plumbing_only", "warning": "No CodeBERT, Tree-sitter DFG, or scientific dataset was used.",
                  "environment": environment_snapshot(), "source": source_identity(ROOT), "manifest_hash": manifest.file_hash}
    atomic_write_json(run_root / "provenance.json", provenance)
    atomic_write_json(run_root / "status.json", {"status": "complete", "models": statuses, "official_test_used": False})
    atomic_write_text(run_root / "command.txt", "python scripts/run_smoke_test.py\n")
    print(json.dumps({"status": "complete", "run_dir": str(run_root), "models": len(statuses), "records": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
