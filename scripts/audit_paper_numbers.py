"""Recompute paper-facing metrics from preserved per-example predictions.

This is a read-only audit except for the requested JSON report. It never opens the
official test role and rejects any intervention report that claims to have done so.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from astguard.evaluation.metrics import average_precision, roc_auc
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _close(left: float | None, right: float | None, tolerance: float = 1e-12) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)


def audit_run(run: Path) -> dict | None:
    predictions = run / "selected_tune_predictions.jsonl"
    selection = run / "checkpoint_selection.json"
    if not predictions.exists() or not selection.exists():
        return None
    rows = _jsonl(predictions)
    if not rows or len({row['sample_id'] for row in rows}) != len(rows):
        raise ValueError(f'empty or duplicate-ID predictions in {predictions}')
    labels = [int(row["label"]) for row in rows]
    scores = [float(row.get("probability", row["logit"])) for row in rows]
    computed_ap = average_precision(labels, scores)
    computed_roc = roc_auc(labels, scores)
    selected = json.loads(selection.read_text(encoding="utf-8"))
    expected_ap = selected.get("best_value") if selected.get("metric") == "average_precision" else None
    return {
        "run_id": run.name,
        "role": selected.get("role"),
        "n_examples": len(rows),
        "n_positive": sum(labels),
        "selected_epoch": selected.get("epoch"),
        "reported_ap": expected_ap,
        "recomputed_ap": computed_ap,
        "recomputed_roc_auc": computed_roc,
        "ap_exact_match_within_1e-12": _close(expected_ap, computed_ap),
        "predictions_sha256": sha256_file(predictions),
        "all_scores_finite": all(math.isfinite(score) for score in scores),
    }


def audit_intervention(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("official_test_used") is not False or report.get("role") != "tune":
        raise ValueError(f"unsafe role metadata in {path}")
    rows = report["predictions"]
    labels = [int(row["label"]) for row in rows]
    fields = sorted(key for key in rows[0] if key.endswith("_logit")) if rows else []
    recomputed = {
        field.removesuffix("_logit") + "_ap": average_precision(labels, [float(row[field]) for row in rows])
        for field in fields
    }
    reported = report.get("metrics", {})
    return {
        "path": str(path),
        "seed": report.get("seed"),
        "variant": report.get("variant"),
        "n_examples": len(rows),
        "n_positive": sum(labels),
        "reported_metrics": reported,
        "recomputed_ap": recomputed,
        "all_reported_ap_match_within_1e-12": all(
            key in reported and _close(value, reported[key]) for key, value in recomputed.items()
        ),
        "report_sha256": sha256_file(path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path, default=Path("runs"))
    parser.add_argument(
        "--interventions-root", type=Path, default=Path("artifacts/release_gates/positive_control_v1_20261006/interventions")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/audits/current_numeric_audit.json")
    )
    args = parser.parse_args(argv)

    runs = [item for run in sorted(args.runs_root.iterdir()) if run.is_dir() if (item := audit_run(run))]
    interventions = []
    if args.interventions_root.exists():
        interventions = [
            audit_intervention(path)
            for path in sorted(args.interventions_root.glob("*.json"))
        ]
    report = {
        "kind": "paper_number_recomputation_audit",
        "official_test_used": None,
        "audit_scope": "metric_recomputation_only_not_split_or_test_certification",
        "evidence_present": bool(runs) and bool(interventions),
        "run_count": len(runs),
        "all_run_ap_match_within_1e-12": all(row["ap_exact_match_within_1e-12"] for row in runs),
        "all_run_scores_finite": all(row["all_scores_finite"] for row in runs),
        "intervention_report_count": len(interventions),
        "all_intervention_ap_match_within_1e-12": all(
            row["all_reported_ap_match_within_1e-12"] for row in interventions
        ),
        "runs": runs,
        "interventions": interventions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(args.output, report)
    print(json.dumps({key: report[key] for key in report if key not in {"runs", "interventions"}}, indent=2))
    return 0 if (
        report["evidence_present"]
        and report["all_run_ap_match_within_1e-12"]
        and report["all_run_scores_finite"]
        and report["all_intervention_ap_match_within_1e-12"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
