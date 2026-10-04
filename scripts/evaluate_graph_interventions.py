"""Evaluate graph-adapter checkpoints under matched counterfactual graphs.

Development roles only. This script intentionally rejects the official test role.
It saves per-example predictions so AP and paired interventions are auditable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True)
    parser.add_argument('--features',required=True)
    parser.add_argument('--checkpoint',required=True)
    parser.add_argument('--role',choices=('train','tune'),default='tune')
    parser.add_argument('--batch-size',type=int,default=16)
    parser.add_argument('--max-examples',type=int)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError('use a new output path; preserve prior intervention evidence')

    import torch
    from torch.utils.data import DataLoader,Subset
    from safetensors.torch import load_model

    from astguard.config import load_config
    from astguard.data.null_graphs import MatchedNullGraphDataset
    from astguard.evaluation.metrics import average_precision
    from astguard.models.factory import create_collator,create_model
    from astguard.train import _FeatureDataset
    from astguard.utils.atomic_io import atomic_write_json
    from astguard.utils.hashing import sha256_file

    config=load_config(args.config,allow_unresolved=True)
    if config.model.variant not in {'graph_adapter','null_centered_graph_adapter'}:
        raise ValueError('graph intervention evaluation requires a graph-adapter variant')
    base=_FeatureDataset(args.features,role=args.role,
                         manifest_hash=config.dataset.manifest_hash,
                         preprocessing_hash=config.preprocessing.cache_hash)
    if args.max_examples is not None:
        base=Subset(base,list(range(min(args.max_examples,len(base)))))
    view=MatchedNullGraphDataset(base,seed=config.training.seed,
                                 samples=config.model.null_graph_samples,
                                 position_blocks=config.model.null_position_blocks,
                                 namespace=f'intervention-{args.role}')
    loader=DataLoader(view,batch_size=args.batch_size,shuffle=False,
                      collate_fn=create_collator(config,training=False))
    model=create_model(config)
    load_model(model,args.checkpoint)
    device='cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device).eval()
    rows=[];change_totals=torch.zeros(2);change_count=0
    with torch.no_grad():
        for batch in loader:
            ids=batch['input_ids'].to(device);attention=batch['attention_mask'].to(device)
            special=batch['special_tokens_mask'].to(device)
            real=batch['relation_masks'].to(device);nulls=batch['null_relation_masks'].to(device)
            normal=model(ids,attention,real,null_relation_masks=nulls,special_tokens_mask=special)
            null_real=model(ids,attention,nulls[:,0],null_relation_masks=nulls,special_tokens_mask=special)
            empty_real=model(ids,attention,torch.zeros_like(real),null_relation_masks=nulls,
                             special_tokens_mask=special)
            base_logits=normal['base_logits'];beta=model.graph_adapter.beta
            uncentered_logits=base_logits+beta*normal['graph_response']
            tensors={
                'normal_logit':normal['logits'],
                'sequence_logit':base_logits,
                'uncentered_logit':uncentered_logits,
                'null_as_real_logit':null_real['logits'],
                'empty_real_logit':empty_real['logits'],
                'structural_correction':normal['structural_correction'],
            }
            cpu={name:value.detach().float().cpu() for name,value in tensors.items()}
            for index,(sample_id,label) in enumerate(zip(batch['sample_ids'],batch['labels'])):
                row={'sample_id':sample_id,'label':int(label)}
                row.update({name:float(value[index]) for name,value in cpu.items()})
                rows.append(row)
            changes=batch['null_graph_change_fractions']
            change_totals+=changes.sum(dim=(0,1));change_count+=changes.shape[0]*changes.shape[1]
    labels=[row['label'] for row in rows]
    logit_fields=[name for name in rows[0] if name.endswith('_logit')] if rows else []
    metrics={name.removesuffix('_logit')+'_ap':average_precision(labels,[row[name] for row in rows])
             for name in logit_fields}
    if rows:
        metrics['mean_abs_structural_correction']=sum(abs(row['structural_correction']) for row in rows)/len(rows)
    report={
        'kind':'development_graph_intervention_evaluation',
        'official_test_used':False,
        'role':args.role,
        'variant':config.model.variant,
        'seed':config.training.seed,
        'n_examples':len(rows),
        'null_graph_samples':config.model.null_graph_samples,
        'null_position_blocks':config.model.null_position_blocks,
        'mean_null_edge_change_fraction':{
            relation:float(change_totals[index]/max(1,change_count))
            for index,relation in enumerate(('ast','dfg'))},
        'metrics':metrics,
        'features_sha256':sha256_file(args.features),
        'checkpoint_sha256':sha256_file(args.checkpoint),
        'predictions':rows,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    atomic_write_json(args.output,report)
    print(json.dumps({key:report[key] for key in
                      ('variant','seed','n_examples','mean_null_edge_change_fraction','metrics')},indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
