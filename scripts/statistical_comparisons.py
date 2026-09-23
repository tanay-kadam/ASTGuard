"""Run registered paired-seed/cluster AP comparisons and Holm correction."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from astguard.analysis.runner import read_rows
from astguard.evaluation.bootstrap import ClusterBootstrap,holm_adjust
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


def _seed_map(paths):
    result={}
    for path in paths:
        rows=read_rows(path)
        seed=int(rows[0]["seed"])
        if seed in result:raise ValueError(f"duplicate seed {seed}")
        result[seed]={row["sample_id"]:row for row in rows}
    return result


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("--plan",required=True,
        help="JSON list: name,left prediction paths,right prediction paths")
    parser.add_argument("--features",required=True);parser.add_argument("--replicates",type=int,default=10000)
    parser.add_argument("--seed",type=int,default=20260921);parser.add_argument("--output",required=True);args=parser.parse_args(argv)
    plan=json.loads(Path(args.plan).read_text(encoding="utf-8"))
    features={row["sample_id"]:row for row in read_rows(args.features)}
    results=[];p_values=[]
    for comparison in plan:
        left,right=_seed_map(comparison["left"]),_seed_map(comparison["right"])
        seeds=sorted(set(left)&set(right))
        if len(seeds)<2:raise ValueError(f"{comparison['name']} has fewer than two paired seeds")
        ids=sorted(set(left[seeds[0]])&set(right[seeds[0]]))
        labels=[int(left[seeds[0]][sample]["label"]) for sample in ids]
        components=[features[sample]["component_id"] for sample in ids]
        left_scores={seed:[float(left[seed][sample]["probability"]) for sample in ids] for seed in seeds}
        right_scores={seed:[float(right[seed][sample]["probability"]) for sample in ids] for seed in seeds}
        result=ClusterBootstrap().hierarchical(labels,left_scores,right_scores,components,
            replicates=args.replicates,seed=args.seed)
        from scipy.stats import ttest_1samp
        p=float(ttest_1samp(result["seed_effects"],0.).pvalue)
        result.update({"name":comparison["name"],"paired_seed_t_p_two_sided":p,
            "left_hashes":[sha256_file(path) for path in comparison["left"]],
            "right_hashes":[sha256_file(path) for path in comparison["right"]],
            "feature_sha256":sha256_file(args.features)})
        p_values.append(p);results.append(result)
    adjusted=holm_adjust(p_values)
    for result,value in zip(results,adjusted):
        result["holm_adjusted_p"]=value
        result["holm_family_size"]=len(results)
    report={"schema_version":"paired-comparisons-v1","analysis_seed":args.seed,
            "bootstrap_replicates":args.replicates,"comparisons":results}
    atomic_write_json(args.output,report);print(args.output);return 0


if __name__=="__main__":raise SystemExit(main())
