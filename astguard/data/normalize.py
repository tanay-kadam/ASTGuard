"""Normalize original split files; validate paired-file IDs against primary rows."""
import argparse
import dataclasses
from collections import Counter,defaultdict
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from astguard.data.adapters import PrimeVulAdapter
from astguard.data.schema import read_jsonl,write_jsonl
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import object_hash


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',default='data/raw/primevul/original')
    parser.add_argument('--output',default='data/interim/primevul')
    args=parser.parse_args()
    root,out=Path(args.root),Path(args.output);out.mkdir(parents=True,exist_ok=True)
    records=[];quarantine=[];paired_diagnostics=[];pairs=[]
    for split in ['train','valid','test']:
        rows,bad=PrimeVulAdapter().read(root/f'primevul_{split}.jsonl','original',split)
        records.extend(rows);quarantine.extend(bad)
        index={row.original_id:row for row in rows}
        groups=defaultdict(list)
        for row in read_jsonl(root/f'primevul_{split}_paired.jsonl'):
            sample=index.get(str(row['idx']))
            if sample is None or sample.source_raw!=row['func'] or sample.label!=row['target']:
                raise ValueError('official paired row does not match its primary sample ID/source/label')
            upstream=row.get('big_vul_idx')
            # Exact upstream identity when supplied. Otherwise retain the whole
            # official project/commit paired group for conservative linkage and
            # mark ambiguous pair membership; never infer row-adjacent pairs.
            key=object_hash([row.get('dataset'),row.get('project'),row.get('commit_id'),upstream])
            groups[key].append(sample)
        for key,members in groups.items():
            pair_id='official-group:'+key
            for member in members: member.pair_ids.append(pair_id)
            if len(members)==2 and {r.label for r in members}=={0,1}:
                vulnerable=next(r for r in members if r.label==1)
                patched=next(r for r in members if r.label==0)
                pairs.append({'pair_id':pair_id,'vulnerable_id':vulnerable.sample_id,'patched_id':patched.sample_id,'split':split})
            else:
                paired_diagnostics.append({'group':key,'status':'ambiguous_membership','member_ids':[r.sample_id for r in members]})
    ids=[r.sample_id for r in records]
    if len(set(ids))!=len(ids):raise ValueError('duplicate original primary IDs')
    write_jsonl(out/'records.jsonl',records)
    pq.write_table(pa.Table.from_pylist([r.to_dict() for r in records]),out/'records.parquet')
    atomic_write_json(out/'quarantine.json',quarantine)
    atomic_write_json(out/'pairs.json',pairs)
    atomic_write_json(out/'pair_diagnostics.json',paired_diagnostics)
    atomic_write_json(out/'normalization_report.json',{'records':len(records),'splits':dict(Counter(r.original_split for r in records)),
        'labels':dict(Counter(r.label for r in records)),'quarantined':len(quarantine),'valid_pair_groups':len(pairs),
        'ambiguous_pair_groups':len(paired_diagnostics)})
    print(f'Normalized {len(records)} records; {len(quarantine)} quarantined; {len(paired_diagnostics)} ambiguous paired groups.')


if __name__=='__main__':main()
