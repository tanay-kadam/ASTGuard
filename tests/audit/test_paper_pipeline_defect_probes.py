"""Regression checks for repaired defects and probes for residual metadata limits."""
import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import torch

from astguard.config import load_config,dump_config
from astguard.data.graph_donors import GraphDonorDataset
from astguard.data.null_graphs import MatchedNullGraphDataset
from astguard.train import _FeatureDataset


def test_actual_training_path_preserves_shuffled_view_for_centered_model(tmp_path,monkeypatch):
    import astguard.train as train
    import astguard.models.factory as factory
    from astguard.training.engine import Trainer
    config=load_config('configs/positive_control/graph_adapter_shuffled.yaml')
    config=dataclasses.replace(config,model=dataclasses.replace(config.model,variant='null_centered_graph_adapter'))
    cfg=tmp_path/'config.json';cfg.write_text(dump_config(config))
    for role in ['train','tune']:
        rows=[]
        for i in range(4):
            rows.append({'sample_id':f'{role}-{i}','component_id':f'{role}-component-{i}',
              'role':role,'label':i%2,'split_hash':config.dataset.manifest_hash,
              'preprocessing_hash':config.preprocessing.cache_hash,
              'input_ids':[0,100,200,2],'attention_mask':[True]*4,'special_tokens_mask':[True,False,False,True],
              'ast_token_edges':[[1,2]] if i%2 else [[2,1]],'dfg_token_edges':[]})
        (tmp_path/f'{role}.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    class Tiny(torch.nn.Module):
        def __init__(self):super().__init__();self.logit=torch.nn.Parameter(torch.tensor(0.0))
    monkeypatch.setattr(factory,'create_model',lambda config:Tiny())
    monkeypatch.setattr(torch.cuda,'is_available',lambda:False)
    captured={}
    def stop_before_fit(self,loader,*args,**kwargs):
        captured['view']=loader.dataset
        raise RuntimeError('audit probe: stop before optimizer updates')
    monkeypatch.setattr(Trainer,'fit',stop_before_fit)
    with pytest.raises(RuntimeError,match='audit probe'):
        train.main(['--config',str(cfg),'--features',str(tmp_path/'train.jsonl'),
                    '--tune-features',str(tmp_path/'tune.jsonl'),'--runs-root',str(tmp_path/'runs')])
    assert isinstance(captured['view'],MatchedNullGraphDataset)
    assert isinstance(captured['view'].base,GraphDonorDataset)
    assert isinstance(captured['view'].base.base,_FeatureDataset)


def test_empty_evidence_fails_numeric_audit(tmp_path):
    root=Path(__file__).resolve().parents[2];runs=tmp_path/'runs';runs.mkdir();interventions=tmp_path/'interventions';interventions.mkdir()
    output=tmp_path/'report.json';env=os.environ.copy();env['PYTHONPATH']=str(root)
    result=subprocess.run([sys.executable,'scripts/audit_paper_numbers.py','--runs-root',str(runs),
        '--interventions-root',str(interventions),'--output',str(output)],cwd=root,env=env,capture_output=True,text=True)
    assert result.returncode==1,result.stderr
    report=json.loads(output.read_text())
    assert report['run_count']==0 and report['all_run_ap_match_within_1e-12'] is True
    assert report['evidence_present'] is False and report['official_test_used'] is None


def test_factory_does_not_forward_attention_relation_override(monkeypatch):
    import astguard.models.factory as factory
    config=load_config('configs/structure_usage/astguard.yaml')
    config=dataclasses.replace(config,model=dataclasses.replace(config.model,relations=('ast',)))
    captured={}
    def record(*args,**kwargs):captured.update(kwargs);return object()
    monkeypatch.setattr(factory.ASTGuardClassifier,'from_pretrained',record)
    factory.create_model(config)
    assert 'relations' not in captured


def test_accumulation_matches_full_group_weighted_gradient():
    from astguard.training.engine import Trainer,weighted_bce_logits
    class Model(torch.nn.Module):
        def __init__(self):super().__init__();self.weight=torch.nn.Parameter(torch.tensor(.3))
        def forward(self,input_ids,attention_mask):return {'logits':self.weight*input_ids[:,0].float()}
    def batch(x,y):return {'input_ids':torch.tensor(x)[:,None],'attention_mask':torch.ones(len(x),1,dtype=torch.bool),'labels':torch.tensor(y)}
    model=Model();reference=Model();weights={0:.6,1:2.0}
    optimizer=torch.optim.SGD(model.parameters(),lr=.01)
    Trainer(model,optimizer,accumulation_steps=2,grad_clip_norm=100).train_epoch([batch([1,2],[0.,1.]),batch([3],[1.])],weights)
    loss=weighted_bce_logits(reference(torch.tensor([[1],[2],[3]]),None)['logits'],torch.tensor([0.,1.,1.]),weights)
    loss.backward();torch.optim.SGD(reference.parameters(),lr=.01).step()
    torch.testing.assert_close(model.weight,reference.weight)
