"""Run registered clean, graph-corruption, or gate-intervention inference."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

from astguard.analysis.robustness import corrupt_feature
from astguard.config import load_config
from astguard.data.schema import read_jsonl
from astguard.evaluation.metrics import decode_threshold,evaluate_scores
from astguard.models.factory import create_collator,create_model
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import object_hash,sha256_file


class _CorruptedDataset:
    def __init__(self,base,condition):
        self.base=base;self.condition=condition
        self.summary={name:{'weighted_achieved':0.,'original_edges':0,'attained':0,'count':0}
                      for name in ('ast','dfg')}
    def __len__(self):return len(self.base)
    def __getitem__(self,index):
        condition=self.condition
        changed,details=corrupt_feature(self.base[index],operation=condition['operation'],
            relation=condition['relation'],rate=float(condition['rate']),seed=int(condition['seed']))
        for relation,detail in details.items():
            summary=self.summary[relation];edges=detail['original_edge_count']
            summary['weighted_achieved']+=detail['achieved_rate']*edges
            summary['original_edges']+=edges;summary['attained']+=int(detail['target_attained']);summary['count']+=1
        return changed


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True);parser.add_argument('--features',required=True)
    parser.add_argument('--manifest',required=True);parser.add_argument('--role',default='test')
    parser.add_argument('--conditions',required=True,help='JSON list of registered inference conditions')
    parser.add_argument('--output-dir');args=parser.parse_args(argv)
    run=Path(args.run);config=load_config(run/'config.resolved.yaml');config_hash=object_hash(dataclasses.asdict(config))
    if args.role in {'test','transfer'}:
        from astguard.protocol import verify_test_lock
        verify_test_lock(run_config=config_hash)
    manifest=json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    expected={sample for sample,role in zip(manifest['ordered_sample_ids'],manifest['roles']) if role==args.role}
    from astguard.train import _FeatureDataset
    rows=_FeatureDataset(args.features,role=args.role,manifest_hash=manifest['file_hash'],
                         preprocessing_hash=config.preprocessing.cache_hash)
    if rows.ids!=expected:raise ValueError('feature population differs from frozen role')
    conditions=json.loads(Path(args.conditions).read_text(encoding='utf-8'))
    thresholds=json.loads((run/'thresholds.json').read_text(encoding='utf-8'))
    checkpoint=run/'checkpoints/best.safetensors';checkpoint_hash=sha256_file(checkpoint)
    if any(entry['checkpoint_hash']!=checkpoint_hash for entry in thresholds.values()):raise ValueError('threshold/checkpoint mismatch')
    import torch
    from torch.utils.data import DataLoader
    from safetensors.torch import load_model
    from astguard.training.engine import Trainer
    model=create_model(config);load_model(model,str(checkpoint));device='cuda' if torch.cuda.is_available() else 'cpu';model.to(device).eval()
    inference=Trainer(model,None,device=device)
    output=Path(args.output_dir or run/'analysis/inference_sweeps');output.mkdir(parents=True,exist_ok=True)
    for condition in conditions:
        kind=condition['type'];condition_id=condition['id'];corrupted=None
        current=rows
        if kind=='corruption':
            corrupted=_CorruptedDataset(rows,condition);current=corrupted
        elif kind not in {'original','gate'}:raise ValueError(f'unknown condition type {kind}')
        loader=DataLoader(current,batch_size=config.training.microbatch_size,shuffle=False,collate_fn=create_collator(config))
        predictions=[]
        with torch.no_grad():
            for batch in loader:
                if kind=='gate':
                    means=condition.get('training_means')
                    if isinstance(means,str):
                        means_path=Path(means.replace('RUN_DIR',str(run)))
                        means={key:torch.tensor(value,device=device) for key,value in json.loads(means_path.read_text()).items()}
                    model.set_gate_intervention(condition['mode'],sample_ids=batch['sample_ids'],seed=int(condition.get('seed',1001)),training_means=means)
                values=inference.forward(batch)['logits'].float().cpu()
                if kind=='gate':model.clear_gate_intervention()
                for sample,label,logit in zip(batch['sample_ids'],batch['labels'],values):
                    probability=float(logit.sigmoid());row={'run_id':run.name,'sample_id':sample,'dataset':config.dataset.name,
                        'view':manifest['view'],'role':args.role,'condition_id':condition_id,'split_hash':manifest['file_hash'],
                        'model_id':config.model.variant,'seed':config.training.seed,'logit':float(logit),'probability':probability,
                        'label':int(label),'checkpoint_hash':checkpoint_hash,'feature_hash':config.preprocessing.cache_hash,
                        'config_hash':config_hash,'threshold_ids':{},'decisions':{}}
                    for name,entry in thresholds.items():
                        threshold=decode_threshold(entry['threshold']);row['threshold_ids'][name]=entry['threshold_id'];row['decisions'][name]=probability>=threshold
                    predictions.append(row)
        metrics={name:evaluate_scores([r['label'] for r in predictions],[r['probability'] for r in predictions],decode_threshold(entry['threshold']))
                 for name,entry in thresholds.items()}
        atomic_write_json(output/(condition_id+'.json'),predictions);atomic_write_json(output/(condition_id+'.metrics.json'),metrics)
        if corrupted is not None:
            aggregate={}
            for relation in ('ast','dfg'):
                detail=corrupted.summary[relation];total=detail['original_edges']
                aggregate[relation]={'edge_weighted_achieved_rate':detail['weighted_achieved']/total if total else 0.,
                                     'original_edges':total,
                                     'target_attained_fraction':detail['attained']/detail['count'] if detail['count'] else None}
            atomic_write_json(output/(condition_id+'.diagnostics.json'),aggregate)
        import pyarrow as pa
        import pyarrow.parquet as pq
        pq.write_table(pa.Table.from_pylist(predictions),output/(condition_id+'.parquet'))
    return 0


if __name__=='__main__':raise SystemExit(main())
