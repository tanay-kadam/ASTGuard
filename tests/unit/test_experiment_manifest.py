import json
from pathlib import Path

from astguard.experiments import dependencies


def test_registered_manifest_is_finite_unique_and_has_materialized_dependencies():
    path=Path(__file__).resolve().parents[2]/"protocol"/"experiment_manifest.jsonl"
    jobs=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(jobs)==200
    assert len({job["job_id"] for job in jobs})==200
    assert all(job["dependencies"]==dependencies(job,jobs) for job in jobs)
    assert all(job["claim_ids"] for job in jobs)


def test_optional_regvd_budget_is_finite():
    path=Path(__file__).resolve().parents[2]/"protocol"/"optional_baseline_manifest.jsonl"
    jobs=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(jobs)==9
    assert all(job["dependencies"]==dependencies(job,jobs) for job in jobs)
