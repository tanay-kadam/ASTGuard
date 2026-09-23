from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.config import load_config
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


def _jobs(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [row["job_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("experiment manifest contains duplicate job IDs")
    known = set(ids)
    for row in rows:
        required = {"job_id", "experiment_id", "model_id", "seed", "stage", "dependencies",
                    "estimated_hours", "host_requirements", "max_retries", "claim_ids", "config"}
        missing = required - set(row)
        if missing:
            raise ValueError(f"{row['job_id']} is missing {sorted(missing)}")
        unknown = set(row["dependencies"]) - known
        if unknown:
            raise ValueError(f"{row['job_id']} has unknown dependencies {sorted(unknown)}")
    return rows


def _verify_checksums(run: Path) -> list[str]:
    path = run / "artifact_checksums.json"
    if not path.exists():
        return ["missing artifact_checksums.json"]
    expected = json.loads(path.read_text(encoding="utf-8"))
    failures = []
    for relative, digest in expected.items():
        artifact = run / relative
        if not artifact.is_file():
            failures.append(f"missing {relative}")
        elif sha256_file(artifact) != digest:
            failures.append(f"checksum mismatch {relative}")
    return failures


def _verify_run(job: dict, run: Path) -> list[str]:
    failures = []
    required = ["config.resolved.yaml", "status.json", "provenance.json", "environment.json",
                "events.jsonl", "checkpoints/best.safetensors", "checkpoint_selection.json"]
    failures.extend(f"missing {name}" for name in required if not (run / name).is_file())
    if failures:
        return failures + _verify_checksums(run)
    status = json.loads((run / "status.json").read_text(encoding="utf-8"))
    if status.get("status") != "complete":
        failures.append(f"run status is {status.get('status')}")
    config = load_config(run / "config.resolved.yaml")
    if config.experiment_id != job["experiment_id"]:
        failures.append("experiment ID mismatch")
    if config.model.variant != job["model_id"]:
        failures.append("model ID mismatch")
    if config.training.seed != int(job["seed"]):
        failures.append("seed mismatch")
    failures.extend(_verify_checksums(run))
    prediction_dir = run / "predictions"
    for prediction in prediction_dir.glob("*.json") if prediction_dir.exists() else []:
        rows = json.loads(prediction.read_text(encoding="utf-8"))
        ids = [row.get("sample_id") for row in rows]
        if len(ids) != len(set(ids)):
            failures.append(f"duplicate prediction IDs in {prediction.name}")
        if any(row.get("model_id") != job["model_id"] or int(row.get("seed", -1)) != int(job["seed"]) for row in rows):
            failures.append(f"prediction provenance mismatch in {prediction.name}")
    return failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="protocol/experiment_manifest.jsonl")
    parser.add_argument("--state-dir", default="artifacts/launcher")
    parser.add_argument("--output", default="artifacts/audits/result_verification.json")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--stages", nargs="+", help="verify only these registered stages")
    args = parser.parse_args(argv)
    jobs = _jobs(Path(args.manifest))
    if args.stages:
        jobs=[job for job in jobs if job["stage"] in set(args.stages)]
        if not jobs:raise ValueError("no manifest jobs match --stages")
    state_dir = Path(args.state_dir)
    results = []
    for job in jobs:
        state_path = state_dir / f"{job['job_id']}.json"
        if not state_path.exists():
            results.append({"job_id": job["job_id"], "status": "missing", "failures": []})
            continue
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            results.append({"job_id": job["job_id"], "status": "invalid", "failures": [str(exc)]})
            continue
        status = state.get("status", "invalid")
        failures = []
        if status == "complete":
            run = Path(state.get("run_dir", ""))
            failures = ["complete state names a missing run directory"] if not run.is_dir() else _verify_run(job, run)
            if failures:
                status = "invalid"
        results.append({"job_id": job["job_id"], "status": status, "failures": failures,
                        "run_dir": state.get("run_dir")})
    counts = Counter(row["status"] for row in results)
    all_complete=counts.get("complete", 0) == len(jobs)
    report = {"status":"passed" if all_complete else "failed",
              "manifest": str(args.manifest), "registered_jobs": len(jobs), "status_counts": dict(counts),
              "verified_complete": counts.get("complete", 0), "all_complete_and_valid": all_complete,
              "scientific_completion_claimed": False, "jobs": results}
    atomic_write_json(args.output, report)
    print(json.dumps({key: value for key, value in report.items() if key != "jobs"}, indent=2))
    if counts.get("invalid", 0) or (args.require_complete and not report["all_complete_and_valid"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
