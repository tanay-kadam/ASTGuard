"""Run the R1 pre-registered parse-status subgroup analysis for the primary comparisons.

Uses the same plan format as `statistical_comparisons.py` (name, left paths,
right paths). Joined test features supply the label-free subgroup status and
dependence components.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.analysis.runner import read_rows
from astguard.analysis.subgroups import INTERPRETATION_RULE, subgroup_comparison
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


def _seed_map(paths):
    result = {}
    for path in paths:
        rows = read_rows(path)
        seed = int(rows[0]["seed"])
        if seed in result:
            raise ValueError(f"duplicate seed {seed}")
        result[seed] = {row["sample_id"]: row for row in rows}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, help="JSON list: name, left prediction paths, right prediction paths")
    parser.add_argument("--features", required=True, help="joined test features with status and component_id")
    parser.add_argument("--replicates", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260921)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    features = {row["sample_id"]: row for row in read_rows(args.features)}
    comparisons = []
    for comparison in plan:
        left, right = _seed_map(comparison["left"]), _seed_map(comparison["right"])
        seeds = sorted(set(left) & set(right))
        if not seeds:
            raise ValueError(f"{comparison['name']} has no paired seeds")
        ids = sorted(set.intersection(*(set(left[s]) & set(right[s]) for s in seeds)))
        if any(len(left[s]) != len(ids) or len(right[s]) != len(ids) for s in seeds):
            raise ValueError(f"{comparison['name']}: prediction sets differ across seeds or models")
        result = subgroup_comparison(ids, features, left, right, replicates=args.replicates, seed=args.seed)
        result.update({"name": comparison["name"],
                       "left_hashes": [sha256_file(path) for path in comparison["left"]],
                       "right_hashes": [sha256_file(path) for path in comparison["right"]]})
        comparisons.append(result)
    report = {"schema_version": "parse-status-subgroups-v1", "protocol_revision": "R1",
              "role": "secondary_descriptive", "interpretation_rule": INTERPRETATION_RULE,
              "analysis_seed": args.seed, "bootstrap_replicates": args.replicates,
              "feature_sha256": sha256_file(args.features), "comparisons": comparisons}
    atomic_write_json(args.output, report)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
