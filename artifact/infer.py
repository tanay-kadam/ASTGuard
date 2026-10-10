"""Rebuild selected architectures offline and check saved FP32 smoke logits.

This is a small weights-to-logits check, not full-cohort re-evaluation or retraining.
"""
import argparse
import gzip
import json
import math
import hashlib
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def read(p):
    with (gzip.open(p,'rt',encoding='utf-8-sig') if p.suffix=='.gz' else p.open(encoding='utf-8-sig')) as f:return json.load(f)
def rows(p):
    with gzip.open(p,'rt') as f:return [json.loads(x) for x in f if x.strip()]

def run(tag,checkpoint,device,limit,full=False,interventions=False,batch_size=4):
    import torch
    from safetensors.torch import load_model
    from transformers import RobertaConfig,RobertaModel
    from astguard.config import load_config
    from astguard.models.codebert import ASTGuardClassifier
    from astguard.models.null_centered import NullCenteredGraphClassifier
    from astguard.data.null_graphs import MatchedNullGraphDataset
    from astguard.models.factory import create_collator
    artifact=ROOT/'artifact';entry=read(artifact/'manifest.json')['jobs'][tag];d=artifact/'evidence'/tag
    asset=read(artifact/'manifest.json')['assets'][entry['checkpoint_asset']]
    digest=hashlib.sha256()
    with checkpoint.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):digest.update(block)
    if checkpoint.stat().st_size!=asset['bytes'] or digest.hexdigest()!=asset['sha256']:raise ValueError('Checkpoint hash mismatch: '+tag)
    cfg=read(d/'config.json');external=entry['family']=='regvd'
    feature=artifact/'smoke_inputs'/('synthetic.jsonl.gz' if entry['family']=='synthetic' else 'real.jsonl.gz')
    if full:
        feature=artifact/'inputs/synthetic/audit.jsonl.gz' if entry['family']=='synthetic' else artifact/'downloads/inputs/real'/('regvd_tune.jsonl' if external else 'tune.jsonl')
        opener=gzip.open if feature.suffix=='.gz' else open
        with opener(feature,'rt') as f:inputs=[json.loads(x) for x in f if x.strip()]
    else:inputs=rows(feature)[:limit]
    if not inputs:raise ValueError('No inference inputs')
    actual_modes={};expected_modes={}
    if external:
        from safetensors import safe_open
        from astguard.baselines.regvd import ReGVDClassifier
        from astguard.baselines.regvd_audit import NativeGraphCollator,native_forward
        with safe_open(str(checkpoint),framework='pt',device='cpu') as f:weight=f.get_tensor('embedding.weight')
        model=ReGVDClassifier(weight);model.gnn.double()
        for layer in model.gnn.layers:layer.weight.data=layer.weight.data.float()
        # ReGVD token IDs differ from CodeBERT; these smoke inputs are separate.
        if not full:inputs=rows(artifact/'smoke_inputs/regvd.jsonl.gz')[:limit]
        load_model(model,str(checkpoint));model.to(device).eval()
        mode='self' if entry['condition']=='self' else 'native'
        for mode in (['native','permuted','empty','self'] if interventions else [mode]):
            actual_modes[mode]=[]
            for start in range(0,len(inputs),batch_size):
                batch=NativeGraphCollator(mode,entry['seed'])(inputs[start:start+batch_size])
                with torch.no_grad():actual_modes[mode].extend(native_forward(model,batch,device).float().cpu().tolist())
            expected_modes[mode]={r['sample_id']:r['logit'] for r in rows(d/(mode+'.jsonl.gz'))}
    else:
        config=load_config(d/'config.json');m=config.model
        raw=read(artifact/'backbone_configs.json')['codebert-base']
        rob=RobertaConfig.from_dict(raw);rob._attn_implementation='eager'
        backbone=RobertaModel(rob,add_pooling_layer=False)
        if m.variant in {'graph_adapter','null_centered_graph_adapter'}:
            model=NullCenteredGraphClassifier(backbone,relations=m.relations,adapter_size=m.graph_adapter_hidden_size,
                head_dropout=m.head_dropout,beta_init=m.beta_init,centered=m.variant=='null_centered_graph_adapter')
        else:
            model=ASTGuardClassifier(backbone,variant=m.variant,structural_layers=m.structural_layers,
                head_dropout=m.head_dropout,beta_init=m.beta_init,gate_sharing=m.gate_sharing,
                freeze_beta=m.freeze_beta,degree_normalization=config.preprocessing.degree_normalization)
        dataset=MatchedNullGraphDataset(inputs,seed=entry['seed'],samples=m.null_graph_samples,
            position_blocks=m.null_position_blocks,namespace='strengthening-'+('audit' if entry['family']=='synthetic' else 'tune'))
        load_model(model,str(checkpoint));model.to(device).eval()
        stored=read(d/'interventions.json.gz');modes=list(stored['metrics']) if interventions else ['normal']
        actual_modes={mode:[] for mode in modes}
        for start in range(0,len(dataset),batch_size):
            batch=create_collator(config)([dataset[i] for i in range(start,min(len(dataset),start+batch_size))])
            kw={};ids=batch['input_ids'].to(device);attention=batch['attention_mask'].to(device)
            if 'relation_masks' in batch:
                real=batch['relation_masks'].to(device);nulls=batch['null_relation_masks'].to(device)
                kw={'special_tokens_mask':batch['special_tokens_mask'].to(device)}
                if m.variant=='null_centered_graph_adapter':kw['null_relation_masks']=nulls
            with torch.no_grad():
                output=model(ids,attention,real,**kw) if 'relation_masks' in batch else model(ids,attention)
                for mode in modes:
                    if mode=='base':value=output.get('base_logits',output['logits'])
                    elif mode=='normal' or 'relation_masks' not in batch:value=output['logits']
                    else:value=model(ids,attention,torch.zeros_like(real) if mode=='empty' else nulls[:,0],**kw)['logits']
                    actual_modes[mode].extend(value.float().cpu().tolist())
        expected_modes={mode:{r['sample_id']:r[mode] for r in stored['predictions']} for mode in modes}
    report={}
    from sklearn.metrics import average_precision_score
    for mode,actual in actual_modes.items():
        expected=expected_modes[mode];deltas=[abs(v-expected[r['sample_id']]) for v,r in zip(actual,inputs)]
        if len(actual)!=len(inputs) or not all(math.isfinite(v) for v in actual):raise ValueError('Invalid inference output')
        report[mode]={'max_abs_logit_error':max(deltas),'mean_abs_logit_error':sum(deltas)/len(deltas)}
        if full:report[mode]['ap']=float(average_precision_score([r['label'] for r in inputs],actual))
    return {'job':tag,'n':len(inputs),'device':device,'full_cohort':full,'modes':report,
            'max_abs_logit_error':max(r['max_abs_logit_error'] for r in report.values())}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jobs',nargs='+',required=True)
    p.add_argument('--checkpoints',type=Path,default=Path('artifact/downloads/checkpoints'));p.add_argument('--device',default='cpu')
    p.add_argument('--examples',type=int,default=4);p.add_argument('--tolerance',type=float,default=1e-4)
    p.add_argument('--full',action='store_true',help='Use complete synthetic audit or downloaded real tune inputs')
    p.add_argument('--interventions',action='store_true',help='Re-run all stored intervention conditions')
    p.add_argument('--batch-size',type=int,default=4)
    p.add_argument('--output',type=Path,default=Path('results/artifact_inference_smoke.json'));a=p.parse_args()
    import torch;torch.set_num_threads(min(torch.get_num_threads(),8))
    results=[]
    for tag in a.jobs:
        if a.batch_size<1 or a.examples<1:p.error('Batch size and examples must be positive')
        r=run(tag,a.checkpoints/(tag+'.safetensors'),a.device,a.examples,a.full,a.interventions,a.batch_size);r['passed']=r['max_abs_logit_error']<=a.tolerance;results.append(r);print(json.dumps(r),flush=True)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'tolerance':a.tolerance,'results':results,'passed':all(r['passed'] for r in results)},indent=2)+'\n')
    raise SystemExit(0 if all(r['passed'] for r in results) else 1)
if __name__=='__main__':main()
