"""Join labels and manifest roles outside the model feature boundary."""
import argparse,json,os
from contextlib import ExitStack
from pathlib import Path
from astguard.data.schema import read_jsonl


def join_features(records_path,features_path,manifest_path,output_path):
    manifest=json.loads(Path(manifest_path).read_text())
    assignments=dict(zip(manifest['ordered_sample_ids'],zip(manifest['roles'],manifest['component_ids'])))
    paths=[records_path] if isinstance(records_path,(str,Path)) else records_path
    labels={row['sample_id']:(row['label'],row['raw_sha256']) for path in paths for row in read_jsonl(path) if row['sample_id'] in assignments}
    output=Path(output_path);output.mkdir(parents=True,exist_ok=True)
    roles=set(manifest['roles']);seen=set()
    with ExitStack() as stack:
        handles={role:stack.enter_context((output/(role+'.jsonl.partial')).open('w',encoding='utf-8',newline='\n')) for role in roles}
        for feature in read_jsonl(features_path):
            sample=feature['sample_id']
            if sample not in assignments:continue
            if sample in seen:raise ValueError('duplicate feature sample ID')
            if sample not in labels:raise ValueError(f'missing source row: {sample}')
            label,source_hash=labels[sample]
            if feature['source_sha256']!=source_hash:raise ValueError(f'feature/source hash mismatch: {sample}')
            seen.add(sample);role,component=assignments[sample]
            row=feature|{'label':label,'role':role,'component_id':component,'split_hash':manifest['file_hash']}
            handles[role].write(json.dumps(row,sort_keys=True,ensure_ascii=False)+'\n')
    if seen!=set(assignments):raise ValueError('missing feature rows in frozen population')
    for role in roles:os.replace(output/(role+'.jsonl.partial'),output/(role+'.jsonl'))
    return {role:str(output/(role+'.jsonl')) for role in sorted(roles)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--records',required=True,nargs='+');parser.add_argument('--features',required=True)
    parser.add_argument('--manifest',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    join_features(args.records,args.features,args.manifest,args.output)


if __name__=='__main__':main()
