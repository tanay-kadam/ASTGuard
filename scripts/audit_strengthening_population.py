"""Audit rebuilt model inputs against corrected source membership; no training."""
import collections
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file,object_hash

ROOT=Path('artifacts/release_gates/strengthening_20261006');DATA=Path('data/strengthening_20261006/real')


def main():
    start=time.time();manifest=json.loads((ROOT/'corrected_manifest.json').read_text())
    assert len({len(manifest[k]) for k in ['ordered_sample_ids','roles','component_ids','original_splits']})==1
    assert object_hash(manifest|{'file_hash':''})==manifest['file_hash']
    assignment={sid:(role,comp,source_split) for sid,role,comp,source_split in zip(manifest['ordered_sample_ids'],manifest['roles'],manifest['component_ids'],manifest['original_splits'])}
    source={};source_roles=collections.defaultdict(set)
    with gzip.open(ROOT/'development_records.jsonl.gz','rt',encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line);sid=row['sample_id'];role,comp,split=assignment[sid]
            assert role in {'train','tune'} and split==row['original_split']
            assert hashlib.sha256(row['source_raw'].encode()).hexdigest()==row['raw_sha256']
            assert sid not in source
            source[sid]=(row['label'],row['raw_sha256'],role,comp)
            source_roles[row['raw_sha256']].add(role)
    assert all(len(roles)==1 for roles in source_roles.values())
    prep=json.loads((DATA/'manifest.json').read_text());report={'split_hash':manifest['file_hash'],'streams':{},'failures':[],
        'source_component_role_preserved':True,'original_test_used':False,'input_overlap':{}}
    sequence_roles=collections.defaultdict(set);full_roles=collections.defaultdict(set)
    for role in ['train','tune']:
        path=DATA/f'{role}.jsonl';count=positive=0;seen=set();status=collections.Counter()
        with path.open() as stream:
            for line in stream:
                row=json.loads(line);sid=row['sample_id'];label,digest,expected_role,component=source[sid]
                assert sid not in seen;seen.add(sid)
                assert (row['label'],row['source_sha256'],row['role'],row['component_id'])==(label,digest,expected_role,component)
                assert expected_role==role and row['split_hash']==manifest['file_hash']
                assert row['preprocessing_hash']==prep['preprocessing_hash']
                n=len(row['input_ids']);assert 2<=n<=512 and row['input_ids'][0]==0 and row['input_ids'][-1]==2
                assert len(row['attention_mask'])==n and all(row['attention_mask'])
                assert row['special_tokens_mask']==[True]+[False]*(n-2)+[True]
                for key in ['ast_token_edges','dfg_token_edges']:
                    assert all(0<a<n-1 and 0<b<n-1 and a!=b for a,b in row[key])
                seq=hashlib.sha256(json.dumps(row['input_ids']).encode()).hexdigest();sequence_roles[seq].add(role)
                full=hashlib.sha256(json.dumps([row['input_ids'],row['ast_token_edges'],row['dfg_token_edges']]).encode()).hexdigest();full_roles[full].add(role)
                count+=1;positive+=label;status[(row['ast_status'],row['dfg_status'])]+=1
                if count%25000==0:print(role,count,round(time.time()-start,1),flush=True)
        assert seen=={sid for sid,(_,_,r,_) in source.items() if r==role}
        assert count==prep['counts'][role] and positive==prep['positives'][role]
        assert sha256_file(path)==prep['hashes'][role]
        report['streams'][role]={'n':count,'positive':positive,'source_membership_labels_and_bounds_valid':True,
            'extraction_status_counts':{f'{a}/{b}':v for (a,b),v in status.items()}}
        external_path=DATA/f'regvd_{role}.jsonl';external_seen=set()
        with external_path.open() as stream:
            for line in stream:
                row=json.loads(line);sid=row['sample_id'];label,digest,expected_role,component=source[sid]
                assert sid not in external_seen;external_seen.add(sid)
                assert (row['label'],row['source_sha256'],row['role'],row['component_id'])==(label,digest,expected_role,component)
                assert expected_role==role and len(row['input_ids'])==400
                assert row['node_ids']==list(dict.fromkeys(row['input_ids']))
                edges={tuple(e) for e in row['native_edges']}
                assert all(0<=a<len(row['node_ids']) and 0<=b<len(row['node_ids']) and a!=b for a,b in edges)
                assert edges=={(b,a) for a,b in edges}
        assert external_seen==seen and sha256_file(external_path)==prep['hashes']['regvd_'+role]
    report['input_overlap']={'sequence_hashes_cross_train_tune':sum(len(v)>1 for v in sequence_roles.values()),
                           'full_model_input_hashes_cross_train_tune':sum(len(v)>1 for v in full_roles.values()),
                           'interpretation':'Truncation can merge different source functions; these counts are representation overlap, not necessarily source/component leakage.'}
    report['audit_checks_passed']=True;report['elapsed_seconds']=time.time()-start
    atomic_write_json(ROOT/'rebuilt_population_audit.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
