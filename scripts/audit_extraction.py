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
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=50);p.add_argument('--output',default='artifacts/audits/extraction_pilot.json')
    p.add_argument('--salt',default='extraction-pilot-v1');p.add_argument('--exclude',help='prior audit JSON whose sample IDs are excluded')
    p.add_argument('--annotation-masking',choices=['a_priori_v1','none'],default='a_priori_v1');args=p.parse_args()
    excluded={s['sample_id'] for s in json.loads(Path(args.exclude).read_text(encoding='utf-8'))['samples']} if args.exclude else set()
    sources=json.loads(Path('artifacts/environment/development_sources.json').read_text())
    tokenizer=CanonicalTokenizer(sources['codebert_path'])
    candidates=[]
    for row in read_jsonl('data/interim/primevul/records.jsonl'):
        if row['original_split']=='train' and row['sample_id'] not in excluded:
            candidates.append((hash_uniform(args.salt,row['sample_id']),row))
    candidates.sort(key=lambda x:x[0])
    results=[];start=time.perf_counter()
    for _,row in candidates:
        feature=preprocess_record(SampleRecord.from_dict(row),tokenizer,annotation_masking=args.annotation_masking)
        if not row['source_canonical'].strip() or feature.original_bpe_length>510:continue
        results.append({'sample_id':row['sample_id'],'language':feature.language_selected,'ast_nonempty':bool(feature.ast_token_edges),
            'dfg_status':feature.dfg_status,'parse_status':feature.parse_status,'reasons':feature.status_reasons,
            'original_bpe_length':feature.original_bpe_length,'ast_edges':len(feature.ast_token_edges),'dfg_edges':len(feature.dfg_token_edges)})
        if len(results)>=args.count:break
    ast=sum(x['ast_nonempty'] for x in results)/len(results)
    dfg=sum(x['dfg_status']=='ok' for x in results)/len(results)
    gates=json.loads(Path('protocol/protocol_v1.json').read_text(encoding='utf-8'))['release_gates']
    passed=ast>=gates['extraction_ast_nonempty_min'] and dfg>=gates['extraction_dfg_supported_min']
    report={'status':'passed' if passed else 'failed','scope':'train_only_hash_sample','release_gates':gates,
        'salt':args.salt,'excluded_prior_audit':args.exclude,'annotation_masking':args.annotation_masking,
        'preprocessing_hash':feature.preprocessing_hash,
        'count':len(results),'ast_nonempty_fraction':ast,'dfg_supported_fraction':dfg,'seconds':time.perf_counter()-start,
        'manual_edge_quality_status':'not_reviewed','language_counts':dict(Counter(x['language'] for x in results)),'samples':results}
    atomic_write_json(args.output,report);print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))


if __name__=='__main__':main()
