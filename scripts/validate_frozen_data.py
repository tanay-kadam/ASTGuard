"""Validate frozen cohort integrity, isolation, class support, and power gates."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from astguard.data.schema import read_jsonl
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import object_hash,sha256_file


def _load_manifest(path):
    doc=json.loads(Path(path).read_text(encoding="utf-8"))
    expected=object_hash(doc|{"file_hash":""})
    if doc.get("file_hash")!=expected:raise ValueError(f"manifest content hash mismatch: {path}")
    return doc


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("--records",nargs="+",required=True)
    parser.add_argument("--p-clean",required=True);parser.add_argument("--p-project",required=True)
    parser.add_argument("--d-transfer",required=True);parser.add_argument("--output",required=True);args=parser.parse_args(argv)
    records={}
    for path in args.records:
        for row in read_jsonl(path):
            if row["sample_id"] in records:raise ValueError(f"duplicate sample ID {row['sample_id']}")
            records[row["sample_id"]]=row
    manifests={name:_load_manifest(path) for name,path in
               (("P_clean",args.p_clean),("P_project",args.p_project),("D_transfer",args.d_transfer))}
    checks={};composition={}
    for name,manifest in manifests.items():
        if manifest["view"]!=name:raise ValueError(f"{name} manifest has wrong view")
        ids=manifest["ordered_sample_ids"];roles=manifest["roles"];components=manifest["component_ids"]
        checks[name+"_ids_exist"]=all(sample_id in records for sample_id in ids)
        by_component={}
        isolated=True
        for component,role in zip(components,roles):
            if component in by_component and by_component[component]!=role:isolated=False
            by_component[component]=role
        checks[name+"_component_isolation"]=isolated
        by_role={}
        for role in sorted(set(roles)):
            selected=[records[sample_id] for sample_id,current in zip(ids,roles) if current==role]
            by_role[role]={"count":len(selected),"positives":sum(int(row["label"]) for row in selected),
                           "negatives":sum(not int(row["label"]) for row in selected),
                           "projects":len({row.get("project_id") or row.get("repository_url") for row in selected
                                           if row.get("project_id") or row.get("repository_url")})}
        composition[name]=by_role
    clean=manifests["P_clean"];clean_roles=dict(zip(clean["ordered_sample_ids"],clean["roles"]))
    original_test={sample_id for sample_id,row in records.items() if row["dataset"]=="primevul" and row["original_split"].lower()=="test"}
    checks["official_test_unchanged"]={sample_id for sample_id,role in clean_roles.items() if role=="test"}==original_test
    for role in ("tune","cal"):
        counts=composition["P_clean"].get(role,{})
        checks[f"P_clean_{role}_both_classes"]=counts.get("positives",0)>0 and counts.get("negatives",0)>0
    transfer=composition["D_transfer"].get("transfer",{})
    project=composition["P_project"].get("test",{})
    interpretation={"D_transfer_confirmatory":transfer.get("positives",0)>=200 and transfer.get("projects",0)>=20,
                    "P_project_confirmatory":project.get("positives",0)>=200 and project.get("projects",0)>=20,
                    "P_clean_tune_rare_operating_point":composition["P_clean"].get("tune",{}).get("positives",0)>=50,
                    "P_clean_cal_rare_operating_point":composition["P_clean"].get("cal",{}).get("positives",0)>=50 and
                        composition["P_clean"].get("cal",{}).get("negatives",0)>=2000}
    status="passed" if all(checks.values()) else "failed"
    report={"status":status,"schema_version":"frozen-data-validation-v1","checks":checks,
            "interpretation_gates":interpretation,"composition":composition,
            "manifest_hashes":{name:sha256_file(path) for name,path in
                (("P_clean",args.p_clean),("P_project",args.p_project),("D_transfer",args.d_transfer))},
            "record_hashes":{path:sha256_file(path) for path in args.records}}
    atomic_write_json(args.output,report);print(json.dumps(report,indent=2))
    return 0 if status=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
