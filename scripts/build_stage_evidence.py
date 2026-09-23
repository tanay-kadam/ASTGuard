"""Assemble content-addressed release-gate evidence without overriding failures."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file

REQUIRED = ("data_integrity", "extraction_gold", "extraction_coverage", "baseline_overfit",
            "model_equivalence", "hpo_complete", "power_diagnostic")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="append", default=[], metavar="NAME=ARTIFACT",
                        help="repeat once for every required release gate")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    supplied = {}
    for value in args.gate:
        if "=" not in value:
            raise ValueError("--gate must use NAME=ARTIFACT")
        name, path = value.split("=", 1)
        if name in supplied:
            raise ValueError(f"duplicate gate {name}")
        supplied[name] = Path(path)
    if set(supplied) != set(REQUIRED):
        raise ValueError(f"required gates are {', '.join(REQUIRED)}")
    output = {}
    for name in REQUIRED:
        path = supplied[name]
        document = json.loads(path.read_text(encoding="utf-8"))
        status = document.get("status")
        if status not in {"passed", "failed"}:
            raise ValueError(f"{name} artifact has no definitive passed/failed status")
        output[name] = {"status": status, "artifact": str(path), "sha256": sha256_file(path)}
    output["status"] = "passed" if all(row["status"] == "passed" for row in output.values()) else "failed"
    atomic_write_json(args.output, output)
    print(json.dumps(output, indent=2))
    return 0 if output["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
