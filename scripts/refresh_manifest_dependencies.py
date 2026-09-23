"""Deterministically materialize launcher dependencies and claim IDs in ledgers."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from astguard.experiments import dependencies
from astguard.utils.atomic_io import atomic_write_text

CLAIMS={
    "E1":["main_ranking","structure_gain","adaptive_gain","low_fpr"],
    "E2":["relation_contribution"],"A1":["mechanism_attribution"],"A2":["mechanism_attribution"],
    "A3":["topology_mechanism"],"A4":["representation_sensitivity"],"A5":["shared_recipe"],
    "A6":["gate_granularity"],"E3":["layer_placement"],"E4":["data_efficiency"],
    "E5":["cross_dataset_transfer"],"E6":["patch_discrimination"],"E7":["corruption_robustness"],
    "E8":["efficiency"],"E9":["gate_behavior"],"E10":["failure_strata"],
    "E10b":["visibility_control"],"E11":["project_generalization"],"E12":["qualitative_errors"],
    "INPUT384":["input_budget_sensitivity"],"B_REGVD":["external_baseline_breadth"],
}


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("manifests",nargs="+");args=parser.parse_args(argv)
    for name in args.manifests:
        path=Path(name)
        jobs=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for job in jobs:
            job["dependencies"]=dependencies(job,jobs)
            job["claim_ids"]=CLAIMS.get(job["experiment_id"],[])
        atomic_write_text(path,"\n".join(json.dumps(job,separators=(",",":")) for job in jobs)+"\n")
        print(f"{path}: {len(jobs)} jobs")
    return 0


if __name__=="__main__":raise SystemExit(main())
