"""Aggregate the frozen topology-positive-control campaign without post-hoc rules."""
from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path


SEEDS = (42, 123, 456)
CONDITIONS = ("authentic", "shuffled", "sequence")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _sample_sd(values: list[float]) -> float:
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    runs: dict[str, dict[int, dict]] = {condition: {} for condition in CONDITIONS}
    for condition in CONDITIONS:
        for seed in SEEDS:
            tag = f"pc_{condition}_s{seed}"
            run_dir = Path((args.campaign_root / "run_dirs" / f"{tag}.txt").read_text(encoding="utf-8").strip())
            status = _read(run_dir / "status.json")
            selection = _read(run_dir / "checkpoint_selection.json")
            if status.get("status") != "complete":
                raise ValueError(f"{tag} is not complete")
            runs[condition][seed] = {
                "run_dir": str(run_dir),
                "selected_epoch": selection["epoch"],
                "ap": float(selection["best_value"]),
            }
    interventions = {}
    rules = {}
    for seed in SEEDS:
        report = _read(args.campaign_root / "interventions" / f"pc_authentic_s{seed}.json")
        if report.get("official_test_used") is not False or report.get("role") != "tune":
            raise ValueError(f"unsafe intervention role for seed {seed}")
        metrics = report["metrics"]
        interventions[seed] = {
            "normal_ap": float(metrics["normal_ap"]),
            "sequence_ap": float(metrics["sequence_ap"]),
            "null_as_real_ap": float(metrics["null_as_real_ap"]),
            "empty_real_ap": float(metrics["empty_real_ap"]),
            "mean_abs_structural_correction": float(metrics["mean_abs_structural_correction"]),
            "mean_null_edge_change_fraction": report["mean_null_edge_change_fraction"],
        }
        authentic = runs["authentic"][seed]["ap"]
        sequence = runs["sequence"][seed]["ap"]
        shuffled = runs["shuffled"][seed]["ap"]
        normal = interventions[seed]["normal_ap"]
        rules[seed] = {
            "authentic_ap_at_least_0_90": authentic >= 0.90,
            "authentic_minus_sequence_at_least_0_30": authentic - sequence >= 0.30,
            "authentic_minus_shuffled_at_least_0_30": authentic - shuffled >= 0.30,
            "normal_minus_empty_at_least_0_30": normal - interventions[seed]["empty_real_ap"] >= 0.30,
            "normal_minus_null_at_least_0_20": normal - interventions[seed]["null_as_real_ap"] >= 0.20,
        }
    summary = {}
    for condition in CONDITIONS:
        values = [runs[condition][seed]["ap"] for seed in SEEDS]
        summary[condition] = {"mean_ap": _mean(values), "sample_sd_ap": _sample_sd(values)}
    report = {
        "kind": "topology_positive_control_v1_summary",
        "official_test_used": False,
        "seeds": list(SEEDS),
        "success_rules_frozen": True,
        "passed": all(all(seed_rules.values()) for seed_rules in rules.values()),
        "runs": runs,
        "interventions": interventions,
        "per_seed_rules": rules,
        "summary": summary,
    }
    _atomic_json(args.output, report)
    print(json.dumps({"passed": report["passed"], "summary": summary, "per_seed_rules": rules}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

