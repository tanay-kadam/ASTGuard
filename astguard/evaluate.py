from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from astguard.evaluation.metrics import evaluate_scores
from astguard.evaluation.thresholds import ThresholdSelector
from astguard.utils.atomic_io import atomic_write_json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--predictions", help="Saved JSON predictions with sample_id,label,probability")
    parser.add_argument('--features',help='Joined feature JSONL for checkpoint inference')
    parser.add_argument('--manifest',required=True,help='Frozen split manifest containing expected IDs/roles')
    parser.add_argument("--split", required=True, choices=["tune","cal","test","transfer"])
    parser.add_argument("--fit-thresholds", action="store_true")
    parser.add_argument("--require-protocol-lock", action="store_true")
    args = parser.parse_args(argv)
    run = Path(args.run)
    from astguard.config import load_config
    from astguard.utils.hashing import object_hash,sha256_file
    import dataclasses
    config=load_config(run/'config.resolved.yaml')
    config_hash=object_hash(dataclasses.asdict(config))
    if args.split in {'test','transfer'} or args.require_protocol_lock:
        from astguard.protocol import verify_test_lock
        verify_test_lock(run_config=config_hash)
    manifest=json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    expected={sample for sample,role in zip(manifest['ordered_sample_ids'],manifest['roles']) if role==args.split}
    if not expected:raise ValueError('manifest has no samples in requested role')
    if args.features:
        from astguard.train import _FeatureDataset
        from astguard.models.factory import create_model,create_collator
        from astguard.training.engine import Trainer
        from safetensors.torch import load_model
        from torch.utils.data import DataLoader
        import torch
        features=_FeatureDataset(args.features,role=args.split,manifest_hash=manifest['file_hash'],
                                 preprocessing_hash=config.preprocessing.cache_hash)
        if features.ids!=expected:raise ValueError('feature population differs from manifest')
        model=create_model(config)
        load_model(model,str(run/'checkpoints/best.safetensors'))
        device='cuda' if torch.cuda.is_available() else 'cpu';model.to(device)
        rows=Trainer(model,None,device=device).predict(DataLoader(features,batch_size=config.training.microbatch_size,collate_fn=create_collator(config)))
        checkpoint_hash=sha256_file(run/'checkpoints/best.safetensors')
        for row in rows:
            row.update({'run_id':run.name,'model_id':config.model.variant,'seed':config.training.seed,'dataset':config.dataset.name,
                'view':manifest['view'],'split_hash':manifest['file_hash'],'config_hash':config_hash,'checkpoint_hash':checkpoint_hash,
                'feature_hash':config.preprocessing.cache_hash,'role':args.split,'metric_version':'1.0'})
        atomic_write_json(run/('calibration_predictions.json' if args.split=='cal' else f'predictions/{args.split}.json'),rows)
    elif args.predictions:
        rows=json.loads(Path(args.predictions).read_text(encoding='utf-8'))
    else:raise ValueError('provide --features or --predictions')
    if len(rows)!=len(expected) or {r['sample_id'] for r in rows}!=expected:raise ValueError('prediction population incomplete or duplicated')
    if any(row.get('role')!=args.split or row.get('config_hash')!=config_hash for row in rows):raise ValueError('prediction role/config provenance mismatch')
    ids = [row["sample_id"] for row in rows]
    labels = [int(row["label"]) for row in rows]
    scores = [float(row["probability"]) for row in rows]
    if args.fit_thresholds:
        if args.split != "cal":
            raise ValueError("--fit-thresholds requires --split cal")
        checkpoint_hash = rows[0]['checkpoint_hash']
        result = ThresholdSelector().fit(ids, labels, scores, role="cal", checkpoint_hash=checkpoint_hash)
        import dataclasses
        atomic_write_json(run / "thresholds.json", {name: dataclasses.asdict(value) for name, value in result.items()})
    else:
        threshold_doc = json.loads((run / "thresholds.json").read_text(encoding="utf-8"))
        from astguard.evaluation.metrics import decode_threshold,official_vds_oracle
        metrics={}
        for name,entry in threshold_doc.items():
            if entry['checkpoint_hash']!=rows[0]['checkpoint_hash']:raise ValueError('threshold checkpoint mismatch')
            threshold=decode_threshold(entry['threshold'])
            metrics[name]=evaluate_scores(labels,scores,threshold)
            for row in rows:
                row.setdefault('threshold_ids',{})[name]=entry['threshold_id']
                row.setdefault('decisions',{})[name]=row['probability']>=threshold
        metrics.update(official_vds_oracle(labels,scores))
        atomic_write_json(run / 'metrics' / f'{args.split}.json',metrics)
        atomic_write_json(run/'predictions'/f'{args.split}.json',rows)
        import pyarrow as pa
        import pyarrow.parquet as pq
        pq.write_table(pa.Table.from_pylist(rows),run/'predictions'/f'{args.split}.parquet')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
