import argparse,dataclasses,json,sys,time
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astguard.data.schema import read_jsonl,SampleRecord
from astguard.data.preprocess import preprocess_record
from astguard.alignment.tokenizer import CanonicalTokenizer
from astguard.utils.hashing import hash_uniform
from astguard.utils.atomic_io import atomic_write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=50);p.add_argument('--output',default='artifacts/audits/extraction_pilot.json');args=p.parse_args()
    sources=json.loads(Path('artifacts/environment/development_sources.json').read_text())
    tokenizer=CanonicalTokenizer(sources['codebert_path'])
    candidates=[]
    for row in read_jsonl('data/interim/primevul/records.jsonl'):
        if row['original_split']=='train':
            candidates.append((hash_uniform('extraction-pilot-v1',row['sample_id']),row))
    candidates.sort(key=lambda x:x[0])
    results=[];start=time.perf_counter()
    for _,row in candidates:
        feature=preprocess_record(SampleRecord.from_dict(row),tokenizer)
        if not row['source_canonical'].strip() or feature.original_bpe_length>510:continue
        results.append({'sample_id':row['sample_id'],'language':feature.language_selected,'ast_nonempty':bool(feature.ast_token_edges),
            'dfg_status':feature.dfg_status,'parse_status':feature.parse_status,'reasons':feature.status_reasons,
            'original_bpe_length':feature.original_bpe_length,'ast_edges':len(feature.ast_token_edges),'dfg_edges':len(feature.dfg_token_edges)})
        if len(results)>=args.count:break
    ast=sum(x['ast_nonempty'] for x in results)/len(results)
    dfg=sum(x['dfg_status']=='ok' for x in results)/len(results)
    report={'status':'passed' if ast>=.9 and dfg>=.6 else 'failed','scope':'train_only_hash_sample',
        'count':len(results),'ast_nonempty_fraction':ast,'dfg_supported_fraction':dfg,'seconds':time.perf_counter()-start,
        'manual_edge_quality_status':'not_reviewed','language_counts':dict(Counter(x['language'] for x in results)),'samples':results}
    atomic_write_json(args.output,report);print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))


if __name__=='__main__':main()
