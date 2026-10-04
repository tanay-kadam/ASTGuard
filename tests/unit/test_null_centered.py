import copy

import torch
from transformers import RobertaConfig, RobertaModel

from astguard.models.null_centered import NullCenteredGraphClassifier
from astguard.training.optim import build_adamw
from astguard.training.engine import Trainer


def _model(centered=True):
    torch.manual_seed(5)
    config = RobertaConfig(vocab_size=64,hidden_size=24,num_attention_heads=4,
                           num_hidden_layers=2,intermediate_size=48,max_position_embeddings=32,
                           hidden_dropout_prob=0.,attention_probs_dropout_prob=0.)
    config._attn_implementation='eager'
    return NullCenteredGraphClassifier(
        RobertaModel(config,add_pooling_layer=False),relations=("ast","dfg"),
        adapter_size=8,head_dropout=0.,beta_init=1.,centered=centered).eval()


def _inputs():
    ids=torch.tensor([[0,5,6,7,2],[0,8,9,2,1]])
    attention=ids.ne(1)
    special=ids.eq(0)|ids.eq(1)|ids.eq(2)
    real=torch.zeros(2,2,5,5,dtype=torch.bool)
    real[0,0,1,2]=real[0,0,2,1]=True
    real[0,1,1,3]=True
    real[1,0,1,2]=real[1,0,2,1]=True
    null=real[:,None].repeat(1,2,1,1,1)
    return ids,attention,special,real,null


def test_identical_real_and_null_cancel_exactly():
    model=_model(centered=True)
    ids,attention,special,real,null=_inputs()
    output=model(ids,attention,real,null_relation_masks=null,special_tokens_mask=special)
    torch.testing.assert_close(output["logits"],output["base_logits"],atol=0,rtol=0)
    torch.testing.assert_close(output["structural_correction"],torch.zeros(2),atol=0,rtol=0)


def test_matched_parameter_control_and_adapter_gradient():
    centered=_model(centered=True)
    uncentered=_model(centered=False)
    uncentered.load_state_dict(copy.deepcopy(centered.state_dict()))
    assert sum(p.numel() for p in centered.parameters()) == sum(p.numel() for p in uncentered.parameters())
    ids,attention,special,real,null=_inputs()
    null=null.clone();null[:,0].zero_()
    logits=centered(ids,attention,real,null_relation_masks=null,special_tokens_mask=special)["logits"]
    logits.sum().backward()
    grads=[p.grad for p in centered.graph_adapter.parameters() if p.grad is not None]
    assert grads and any(torch.isfinite(g).all() and g.abs().sum()>0 for g in grads)


def test_graph_adapter_uses_new_module_learning_rate():
    model=_model(centered=True)
    optimizer=build_adamw(model,pretrained_lr=2e-5,new_multiplier=10,weight_decay=.01)
    lr_by_parameter={id(parameter):group["lr"] for group in optimizer.param_groups for parameter in group["params"]}
    assert all(lr_by_parameter[id(parameter)] == 2e-4 for parameter in model.graph_adapter.parameters())
    assert lr_by_parameter[id(next(model.backbone.parameters()))] == 2e-5


def test_trainer_predictions_preserve_structural_diagnostics():
    model=_model(centered=True)
    ids,attention,special,real,null=_inputs()
    batch={'input_ids':ids,'attention_mask':attention,'special_tokens_mask':special,
           'relation_masks':real,'null_relation_masks':null,
           'labels':torch.tensor([1.,0.]),'sample_ids':['a','b']}
    trainer=Trainer(model,torch.optim.SGD(model.parameters(),lr=.01))
    rows=trainer.predict([batch])
    assert [row['sample_id'] for row in rows] == ['a','b']
    assert all('base_logits' in row and 'structural_correction' in row for row in rows)
