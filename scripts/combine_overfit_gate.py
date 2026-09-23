"""Combine per-model overfit checks into the single baseline_overfit release-gate artifact."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file

REQUIRED_MODELS = ("sequence_only", "ast_dfg_fixed", "astguard")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    models = {}
    for path in map(Path, args.result):
        document = json.loads(path.read_text(encoding="utf-8"))
        models[document["model_id"]] = {"status": document["status"], "accuracy": document["accuracy"],
                                        "optimizer_steps": document["optimizer_steps"],
                                        "config_hash": document["config_hash"], "device": document["device"],
                                        "artifact": str(path), "sha256": sha256_file(path)}
    missing = set(REQUIRED_MODELS) - set(models)
    if missing:
        raise ValueError(f"missing overfit results for {sorted(missing)}")
    status = "passed" if all(row["status"] == "passed" for row in models.values()) else "failed"
    atomic_write_json(args.output, {"status": status, "models": models})
    print(json.dumps({"status": status, "models": sorted(models)}))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
