import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
from transformers import RobertaModel
from astguard.models.codebert import ASTGuardClassifier
from astguard.alignment.tokenizer import CanonicalTokenizer
from astguard.utils.atomic_io import atomic_write_json


def main():
    torch.set_num_threads(2)
    sources=json.loads(Path('artifacts/environment/development_sources.json').read_text())
    tokenizer=CanonicalTokenizer(sources['codebert_path'])
    encoded=tokenizer.encode('int f(int x) { return x + 1; }')
    ids=torch.tensor([encoded.input_ids]); mask=torch.ones_like(ids)
    backbone=RobertaModel.from_pretrained(sources['codebert_path'],add_pooling_layer=False,attn_implementation='eager').eval()
    with torch.no_grad():
        expected=backbone(ids,attention_mask=mask,output_hidden_states=True)
    model=ASTGuardClassifier(backbone,beta_init=0.).eval()
    relations=torch.zeros(1,2,ids.shape[1],ids.shape[1],dtype=torch.bool)
    relations[0,0,1,2]=True
    with torch.no_grad():
        actual=model(ids,mask,relations,output_hidden_states=True)
    errors=[]
    for left,right in zip(actual['hidden_states'],expected.hidden_states):
        torch.testing.assert_close(left,right,atol=1e-6,rtol=1e-5)
        errors.append(float((left-right).abs().max()))
    torch.testing.assert_close(actual['logits'],model.classifier(expected.last_hidden_state),atol=1e-6,rtol=1e-5)
    atomic_write_json('artifacts/audits/pretrained_equivalence.json',{'status':'passed','revision':sources['codebert_revision'],
        'hidden_layer_max_absolute_errors':errors,'device':'cpu','precision':'fp32','atol':1e-6,'rtol':1e-5})
    print('Pretrained CodeBERT: all hidden states and logits pass FP32 equivalence.')


if __name__=='__main__':main()
