"""Build F3 precision-recall curves and vulnerable/patched logit margins."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from astguard.analysis.runner import read_rows
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


REQUIRED={"sample_id","label","probability","logit","model_id","seed","split_hash","role"}


def build_rows(prediction_paths,pair_path=None):
    from sklearn.metrics import precision_recall_curve
    pr_rows=[];margin_rows=[];provenance=[]
    pairs=read_rows(pair_path) if pair_path else []
    for prediction_path in prediction_paths:
        rows=read_rows(prediction_path)
        if not rows or any(REQUIRED-set(row) for row in rows):
            raise ValueError(f"{prediction_path} is empty or lacks common prediction fields")
        if len({row["sample_id"] for row in rows})!=len(rows):
            raise ValueError(f"duplicate prediction IDs in {prediction_path}")
        identity={(row["model_id"],int(row["seed"]),row["split_hash"],row["role"]) for row in rows}
        if len(identity)!=1:raise ValueError(f"mixed run identity in {prediction_path}")
        model,seed,split_hash,role=identity.pop()
        labels=[int(row["label"]) for row in rows];scores=[float(row["probability"]) for row in rows]
        if len(set(labels))!=2:raise ValueError(f"PR curve requires both classes: {prediction_path}")
        precision,recall,thresholds=precision_recall_curve(labels,scores)
        for index,(p,r) in enumerate(zip(precision,recall)):
            pr_rows.append({"model_id":model,"seed":seed,"point_index":index,"precision":float(p),
                            "recall":float(r),"threshold":float(thresholds[index]) if index<len(thresholds) else None,
                            "split_hash":split_hash,"role":role})
        by_id={row["sample_id"]:row for row in rows}
        for pair in pairs:
            vulnerable=by_id.get(pair["vulnerable_id"]);patched=by_id.get(pair["patched_id"])
            if vulnerable is None or patched is None:continue
            margin_rows.append({"model_id":model,"seed":seed,"pair_id":pair["pair_id"],
                                "logit_margin":float(vulnerable["logit"])-float(patched["logit"]),
                                "correct_order":float(vulnerable["logit"])>float(patched["logit"]),
                                "split_hash":split_hash,"role":role})
        provenance.append({"path":str(prediction_path),"sha256":sha256_file(prediction_path)})
    return pr_rows,margin_rows,{"predictions":provenance,"pairs":({"path":str(pair_path),"sha256":sha256_file(pair_path)} if pair_path else None)}


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("--predictions",nargs="+",required=True)
    parser.add_argument("--pairs");parser.add_argument("--output-dir",required=True);args=parser.parse_args(argv)
    pr_rows,margin_rows,provenance=build_rows(args.predictions,args.pairs)
    output=Path(args.output_dir);output.mkdir(parents=True,exist_ok=True)
    atomic_write_json(output/"pr_curve_rows.json",pr_rows)
    atomic_write_json(output/"pair_margin_rows.json",margin_rows)
    atomic_write_json(output/"f3_provenance.json",provenance)
    print(json.dumps({"pr_points":len(pr_rows),"pair_margins":len(margin_rows),"output":str(output)},indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
