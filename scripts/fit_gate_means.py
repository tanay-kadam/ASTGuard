"""Fit registered A2 layer/head/relation gate means on training IDs only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from astguard.config import load_config
from astguard.data.schema import read_jsonl
from astguard.models.factory import create_collator,create_model
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import hash_uniform


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--train-features',required=True)
    parser.add_argument('--count',type=int,default=10000);parser.add_argument('--output');args=parser.parse_args(argv)
    run=Path(args.run);config=load_config(run/'config.resolved.yaml')
    rows=[row for row in read_jsonl(args.train_features) if row.get('role')=='train']
    rows=sorted(rows,key=lambda row:(hash_uniform('gate-mean-v1',row['sample_id']),row['sample_id']))[:args.count]
    if not rows:raise ValueError('no training features')
    import torch
    from torch.utils.data import DataLoader
    from safetensors.torch import load_model
    model=create_model(config);load_model(model,str(run/'checkpoints/best.safetensors'))
    if not hasattr(model,'layers'):raise ValueError('gate means require an adaptive controlled model')
    device='cuda' if torch.cuda.is_available() else 'cpu';model.to(device).eval()
    totals={};counts={}
    loader=DataLoader(rows,batch_size=config.training.microbatch_size,shuffle=False,collate_fn=create_collator(config))
    relation_index={'ast':0,'dfg':1};selected=[relation_index[name] for name in model.relations]
    with torch.no_grad():
        for batch in loader:
            relation_masks=batch['relation_masks'].to(device)[:,selected]
            model(batch['input_ids'].to(device),batch['attention_mask'].to(device),batch['relation_masks'].to(device),
                  special_tokens_mask=batch['special_tokens_mask'].to(device),output_attentions=True)
            eligible=relation_masks.sum(-1).permute(0,2,1).gt(0)[:,None]
            for index,layer in enumerate(model.layers):
                diagnostics=getattr(layer.structural_attention,'last_diagnostics',None) if layer.structural_attention else None
                if not diagnostics or diagnostics['gates'] is None:continue
                gates=diagnostics['gates'];weight=eligible.to(gates.dtype)
                totals[index]=totals.get(index,torch.zeros_like(gates.sum((0,2))))+(gates*weight).sum((0,2))
                counts[index]=counts.get(index,torch.zeros_like(weight.sum((0,2))))+weight.sum((0,2))
    means={str(index):(totals[index]/counts[index].clamp_min(1)).cpu().tolist() for index in totals}
    output=Path(args.output or run/'analysis/gates/training_means.json');output.parent.mkdir(parents=True,exist_ok=True)
    atomic_write_json(output,means);print(output);return 0


if __name__=='__main__':raise SystemExit(main())
