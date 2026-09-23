"""Aggregate registered A2/E7 sweeps from saved predictions and diagnostics."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from astguard.analysis.runner import read_rows,trapezoidal_area
from astguard.evaluation.metrics import average_precision
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


def _achieved(path:Path,relation:str)->float:
    if not path.exists():return 0.
    doc=json.loads(path.read_text(encoding="utf-8"))
    names=("ast","dfg") if relation=="both" else (relation,)
    total=sum(doc.get(name,{}).get("original_edges",0) for name in names)
    return (sum(doc.get(name,{}).get("edge_weighted_achieved_rate",0)*doc.get(name,{}).get("original_edges",0)
                for name in names)/total) if total else 0.


def _clip(points,bound):
    points=sorted(points)
    kept=[point for point in points if point[0]<=bound]
    if kept and kept[-1][0]<bound:
        right=next((point for point in points if point[0]>bound),None)
        if right:
            left=kept[-1];fraction=(bound-left[0])/(right[0]-left[0])
            kept.append((bound,left[1]+fraction*(right[1]-left[1])))
    return kept


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("--sweep-dirs",nargs="+",required=True)
    parser.add_argument("--conditions",required=True);parser.add_argument("--output-dir",required=True);args=parser.parse_args(argv)
    conditions={row["id"]:row for row in json.loads(Path(args.conditions).read_text(encoding="utf-8"))}
    corruption=[];interventions=[]
    for directory_name in args.sweep_dirs:
        directory=Path(directory_name)
        for condition_id,condition in conditions.items():
            path=directory/(condition_id+".json")
            if not path.exists():continue
            rows=read_rows(path)
            if not rows:continue
            labels=[int(row["label"]) for row in rows];scores=[float(row["probability"]) for row in rows]
            base={"run_id":rows[0]["run_id"],"model_id":rows[0]["model_id"],"model_seed":int(rows[0]["seed"]),
                  "condition_id":condition_id,"average_precision":average_precision(labels,scores),
                  "prediction_sha256":sha256_file(path)}
            if condition["type"]=="corruption":
                corruption.append(base|{"operation":condition["operation"],"relation":condition["relation"],
                    "requested_rate":float(condition["rate"]),"corruption_seed":int(condition["seed"]),
                    "achieved_rate":_achieved(directory/(condition_id+".diagnostics.json"),condition["relation"])})
            elif condition["type"]=="gate":
                interventions.append(base|{"mode":condition["mode"],"intervention_seed":condition.get("seed")})
            elif condition["type"]=="original":
                interventions.append(base|{"mode":"original","intervention_seed":None})
                for operation in ("delete","swap"):
                    for relation in ("ast","dfg","both"):
                        corruption.append(base|{"operation":operation,"relation":relation,"requested_rate":0.,
                            "corruption_seed":None,"achieved_rate":0.})
    averaged=[]
    grouped=defaultdict(list)
    for row in corruption:
        grouped[(row["run_id"],row["model_id"],row["model_seed"],row["operation"],row["relation"],row["requested_rate"])].append(row)
    for key,rows in sorted(grouped.items()):
        averaged.append({"run_id":key[0],"model_id":key[1],"model_seed":key[2],"operation":key[3],"relation":key[4],
                         "requested_rate":key[5],"repeat_count":len(rows),
                         "achieved_rate":statistics.mean(row["achieved_rate"] for row in rows),
                         "average_precision":statistics.mean(row["average_precision"] for row in rows)})
    curves=defaultdict(list)
    for row in averaged:
        curves[(row["run_id"],row["model_id"],row["model_seed"],row["operation"],row["relation"])].append(
            (row["achieved_rate"],row["average_precision"]))
    family_max=defaultdict(list)
    for key,points in curves.items():family_max[(key[3],key[4])].append(max(x for x,_ in points))
    areas=[]
    for key,points in sorted(curves.items()):
        common_max=min(family_max[(key[3],key[4])])
        area=trapezoidal_area(_clip(points,common_max))
        areas.append({"run_id":key[0],"model_id":key[1],"model_seed":key[2],"operation":key[3],"relation":key[4],
                      "common_maximum_achieved_rate":common_max,**area})
    intervention_groups=defaultdict(list)
    for row in interventions:
        intervention_groups[(row["run_id"],row["model_id"],row["model_seed"],row["mode"])].append(row)
    intervention_summary=[]
    for key,rows in sorted(intervention_groups.items()):
        intervention_summary.append({"run_id":key[0],"model_id":key[1],"model_seed":key[2],"mode":key[3],
                                     "repeat_count":len(rows),
                                     "average_precision":statistics.mean(row["average_precision"] for row in rows),
                                     "prediction_hashes":sorted(row["prediction_sha256"] for row in rows)})
    output=Path(args.output_dir);output.mkdir(parents=True,exist_ok=True)
    atomic_write_json(output/"robustness.json",{"raw":corruption,"repeat_averages":averaged,"common_range_areas":areas})
    atomic_write_json(output/"interventions.json",{"raw":interventions,"repeat_averages":intervention_summary})
    print(output);return 0


if __name__=="__main__":raise SystemExit(main())
