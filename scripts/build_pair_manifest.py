"""Freeze unambiguous vulnerable/patched pairs from normalized release metadata."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from astguard.data.schema import read_jsonl,write_jsonl
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import object_hash,sha256_file


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("--records",nargs="+",required=True)
    parser.add_argument("--manifest",required=True);parser.add_argument("--role",default="test")
    parser.add_argument("--output",required=True);args=parser.parse_args(argv)
    manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    roles=dict(zip(manifest["ordered_sample_ids"],manifest["roles"]))
    groups=defaultdict(list)
    for path in args.records:
        for row in read_jsonl(path):
            if roles.get(row["sample_id"])!=args.role:continue
            for pair_id in row.get("pair_ids",[]):groups[pair_id].append(row)
    pairs=[];exclusions={}
    for pair_id,members in sorted(groups.items()):
        unique={row["sample_id"]:row for row in members}
        vulnerable=sorted(row["sample_id"] for row in unique.values() if int(row["label"])==1)
        patched=sorted(row["sample_id"] for row in unique.values() if int(row["label"])==0)
        if len(vulnerable)!=1 or len(patched)!=1 or len(unique)!=2:
            exclusions[pair_id]={"reason":"pair_not_exactly_one_vulnerable_and_one_patched",
                                 "member_ids":sorted(unique),"labels":[int(unique[key]["label"]) for key in sorted(unique)]}
            continue
        pairs.append({"pair_id":pair_id,"vulnerable_id":vulnerable[0],"patched_id":patched[0],
                      "role":args.role,"split_hash":manifest["file_hash"]})
    write_jsonl(args.output,pairs)
    report={"status":"passed" if pairs else "failed","view":manifest["view"],"role":args.role,
            "pair_count":len(pairs),"excluded_pair_count":len(exclusions),"exclusions":exclusions,
            "manifest_sha256":sha256_file(args.manifest),"pair_manifest_sha256":sha256_file(args.output),
            "pair_population_hash":object_hash(pairs)}
    atomic_write_json(Path(args.output).with_suffix(".report.json"),report)
    print(json.dumps({key:value for key,value in report.items() if key!="exclusions"},indent=2))
    return 0 if pairs else 1


if __name__=="__main__":raise SystemExit(main())
