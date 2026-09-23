"""Pre-test paired-seed AP power diagnostic on V_tune predictions."""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from astguard.analysis.runner import read_rows
from astguard.evaluation.metrics import average_precision
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


def _models(paths):
    result={}
    for path in paths:
        rows=read_rows(path)
        if not rows:raise ValueError(f"empty predictions: {path}")
        seed=int(rows[0]["seed"])
        if seed in result:raise ValueError(f"duplicate seed {seed}")
        result[seed]={row["sample_id"]:row for row in rows}
    return result


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("--adaptive",nargs="+",required=True)
    parser.add_argument("--fixed",nargs="+",required=True);parser.add_argument("--target-power",type=float,default=.80)
    parser.add_argument("--alpha",type=float,default=.05);parser.add_argument("--output",required=True);args=parser.parse_args(argv)
    adaptive,fixed=_models(args.adaptive),_models(args.fixed)
    seeds=sorted(set(adaptive)&set(fixed))
    if len(seeds)<3:raise ValueError("power diagnostic requires at least three paired seeds")
    effects=[];population=None
    for seed in seeds:
        ids=sorted(set(adaptive[seed])&set(fixed[seed]))
        if population is None:population=ids
        elif ids!=population:raise ValueError("paired-seed prediction populations differ")
        labels=[int(adaptive[seed][sample]["label"]) for sample in ids]
        if any(int(fixed[seed][sample]["label"])!=label for sample,label in zip(ids,labels)):raise ValueError("label mismatch")
        left=average_precision(labels,[adaptive[seed][sample]["probability"] for sample in ids])
        right=average_precision(labels,[fixed[seed][sample]["probability"] for sample in ids])
        if left is None or right is None:raise ValueError("V_tune population lacks a class")
        effects.append(left-right)
    mean=statistics.mean(effects);sd=statistics.stdev(effects)
    if sd==0:
        power=1. if mean!=0 else args.alpha
    else:
        from scipy.stats import nct,t
        df=len(effects)-1;critical=t.ppf(1-args.alpha/2,df);noncentral=mean/(sd/math.sqrt(len(effects)))
        power=float(nct.sf(critical,df,noncentral)+nct.cdf(-critical,df,noncentral))
    status="passed" if power>=args.target_power else "failed"
    report={"status":status,"schema_version":"pretest-power-v1","paired_seeds":seeds,
            "seed_effects":effects,"mean_ap_difference":mean,"sample_sd":sd,
            "estimated_two_sided_paired_t_power":power,"target_power":args.target_power,
            "alpha":args.alpha,"sample_count":len(population or []),
            "adaptive_prediction_hashes":[sha256_file(path) for path in args.adaptive],
            "fixed_prediction_hashes":[sha256_file(path) for path in args.fixed],
            "action_if_failed":"freeze an equal seed expansion for sequence/fixed/adaptive before test access"}
    atomic_write_json(args.output,report);print(json.dumps(report,indent=2));return 0 if status=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
