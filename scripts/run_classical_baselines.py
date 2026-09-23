from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
import uuid
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

from astguard.baselines.classical import PriorAdapter,TfidfAdapter
from astguard.data.schema import read_jsonl
from astguard.evaluation.metrics import evaluate_scores
from astguard.evaluation.thresholds import ThresholdSelector
from astguard.utils.atomic_io import atomic_write_json,atomic_write_text
from astguard.utils.hashing import object_hash,sha256_file


def decorate(rows,*,run_id,model_id,manifest,checkpoint_hash,thresholds=None):
    from astguard.evaluation.metrics import decode_threshold
    output=[]
    for row in rows:
        value=dict(row);value.update({'run_id':run_id,'model_id':model_id,'seed':42,
            'dataset':'primevul','view':manifest['view'],'split_hash':manifest['file_hash'],
            'checkpoint_hash':checkpoint_hash,'metric_version':'1.0'})
        if thresholds:
            value['threshold_ids']={name:item['threshold_id'] for name,item in thresholds.items()}
            value['decisions']={name:value['probability']>=decode_threshold(item['threshold']) for name,item in thresholds.items()}
        output.append(value)
    return output


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--records',required=True,nargs='+')
    parser.add_argument('--manifest',required=True)
    parser.add_argument('--checkpoint',required=True)
    parser.add_argument('--revision')
    parser.add_argument('--baselines',nargs='+',choices=['prior','tfidf_lr'],default=['prior','tfidf_lr'])
    parser.add_argument('--runs-root',default='runs')
    parser.add_argument('--evaluate-test',action='store_true')
    args=parser.parse_args(argv)
    manifest=json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    assignments=dict(zip(manifest['ordered_sample_ids'],manifest['roles']))
    grouped={role:[] for role in set(manifest['roles'])}
    for path in args.records:
        for row in read_jsonl(path):
            role=assignments.get(row['sample_id'])
            if role:grouped[role].append(row|{'role':role})
    if any(len(grouped.get(role,[]))==0 for role in ('train','tune','cal')):raise ValueError('train/tune/cal populations are required')
    if args.evaluate_test:
        from astguard.protocol import verify_test_lock
        verify_test_lock()
    tokenizer=None
    if 'tfidf_lr' in args.baselines:
        from astguard.alignment.tokenizer import CanonicalTokenizer
        tokenizer=CanonicalTokenizer(args.checkpoint,args.revision)
    for name in args.baselines:
        adapter=PriorAdapter() if name=='prior' else TfidfAdapter(tokenizer)
        run_id=f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{name}-42-{uuid.uuid4().hex[:6]}"
        run_dir=Path(args.runs_root)/run_id;run_dir.mkdir(parents=True,exist_ok=False)
        selection=adapter.fit(grouped['train'],grouped['tune'])
        import joblib
        model_path=run_dir/'model.joblib';joblib.dump(adapter,model_path)
        checkpoint_hash=sha256_file(model_path)
        cal=adapter.predict_to_common_schema(grouped['cal'])
        fitted=ThresholdSelector().fit([r['sample_id'] for r in cal],[r['label'] for r in cal],[r['probability'] for r in cal],
                                       role='cal',checkpoint_hash=checkpoint_hash)
        threshold_doc={key:dataclasses.asdict(value) for key,value in fitted.items()}
        atomic_write_json(run_dir/'thresholds.json',threshold_doc)
        for role in ['tune','cal']+(['test'] if args.evaluate_test else []):
            raw=adapter.predict_to_common_schema(grouped[role]);rows=decorate(raw,run_id=run_id,model_id=name,
                manifest=manifest,checkpoint_hash=checkpoint_hash,thresholds=threshold_doc)
            target=run_dir/'predictions';target.mkdir(exist_ok=True)
            atomic_write_json(target/(role+'.json'),rows)
            import pyarrow as pa
            import pyarrow.parquet as pq
            pq.write_table(pa.Table.from_pylist(rows),target/(role+'.parquet'))
            metrics={rule:evaluate_scores([r['label'] for r in rows],[r['probability'] for r in rows],
                math.inf if entry['threshold']=='+infinity' else float(entry['threshold'])) for rule,entry in threshold_doc.items()}
            (run_dir/'metrics').mkdir(exist_ok=True);atomic_write_json(run_dir/'metrics'/(role+'.json'),metrics)
        config={'model_id':name,'seed':42,'manifest_hash':manifest['file_hash'],'checkpoint_revision':args.revision,
                'selection':selection,'provenance':adapter.provenance()}
        atomic_write_json(run_dir/'config.resolved.json',config)
        atomic_write_text(run_dir/'command.txt',' '.join(sys.argv)+'\n')
        atomic_write_json(run_dir/'status.json',{'status':'complete','run_id':run_id,'official_test_used':args.evaluate_test})
        atomic_write_json(run_dir/'artifact_checksums.json',{str(p.relative_to(run_dir)).replace('\\','/'):sha256_file(p)
            for p in sorted(run_dir.rglob('*')) if p.is_file() and p.name!='artifact_checksums.json'})
        print(run_dir)
    return 0


if __name__=='__main__':raise SystemExit(main())
