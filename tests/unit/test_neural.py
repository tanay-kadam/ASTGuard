import copy

import pytest
import torch
from transformers import RobertaConfig, RobertaModel

from astguard.models.codebert import ASTGuardClassifier
from astguard.training.engine import Trainer, weighted_bce_logits


def setup_model(variant='astguard', beta=None):
    torch.manual_seed(17)
    config = RobertaConfig(vocab_size=128, hidden_size=32, num_attention_heads=4,
                           num_hidden_layers=2, intermediate_size=64, max_position_embeddings=80,
                           hidden_dropout_prob=0., attention_probs_dropout_prob=0.)
    config._attn_implementation = 'eager'
    base = RobertaModel(config, add_pooling_layer=False)
    reference = copy.deepcopy(base)
    torch.manual_seed(42)
    model = ASTGuardClassifier(base, variant=variant, structural_layers=(0,1), head_dropout=0., beta_init=beta, plumbing_only=True)
    return model.eval(), reference.eval()


def inputs():
    ids = torch.tensor([[0,5,6,2], [0,7,2,1]])
    mask = ids != 1
    relations = torch.zeros(2,2,4,4,dtype=torch.bool)
    relations[0,0,1,2] = relations[0,0,2,1] = True
    relations[0,1,2,1] = True
    specials = (ids == 0) | (ids == 1) | (ids == 2)
    return ids, mask, relations, specials


def test_zero_bias_all_hidden_states_match_upstream():
    model, ref = setup_model(beta=0.)
    ids, mask, relations, specials = inputs()
    with torch.no_grad():
        actual = model(ids,mask,relations,output_hidden_states=True)
        expected = ref(ids,attention_mask=mask,output_hidden_states=True)
    for left,right in zip(actual['hidden_states'], expected.hidden_states):
        torch.testing.assert_close(left,right,atol=1e-6,rtol=1e-5)
    torch.testing.assert_close(actual['logits'],model.classifier(expected.last_hidden_state),atol=1e-6,rtol=1e-5)


def test_matched_fixed_adaptive_initialization_and_gradients():
    fixed,_ = setup_model('ast_dfg_fixed')
    adaptive,_ = setup_model()
    ids,mask,relations,specials = inputs()
    a = adaptive(ids,mask,relations)['logits']
    b = fixed(ids,mask,relations)['logits']
    torch.testing.assert_close(a,b,atol=1e-6,rtol=1e-5)
    loss = weighted_bce_logits(a,torch.tensor([1.,0.]),{0:1.,1:1.})
    loss.backward()
    gate = adaptive.layers[0].structural_attention.gate.projection.weight.grad
    beta = adaptive.layers[0].structural_attention.beta.grad
    assert torch.isfinite(gate).all() and gate.abs().sum() > 0
    assert torch.isfinite(beta).all() and beta.abs().sum() > 0


@pytest.mark.parametrize('variant',['sequence_only','fixed_adapter','linear_relation','function_gate','astguard_ast_only','astguard_dfg_only'])
def test_controls_forward_backward(variant):
    model,_ = setup_model(variant)
    ids,mask,relations,specials = inputs()
    output = model(ids,mask,relations,special_tokens_mask=specials)
    assert output['logits'].shape == (2,)
    output['logits'].sum().backward()
    assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)


def test_padding_invariance_and_empty_graph():
    model,_ = setup_model()
    ids,mask,relations,specials = inputs()
    batch = model(ids,mask,relations)['logits']
    single = model(ids[1:,:3],mask[1:,:3],relations[1:,:,:3,:3])['logits']
    torch.testing.assert_close(batch[1:],single,atol=1e-6,rtol=1e-5)
    empty = model(ids,mask,torch.zeros_like(relations))['logits']
    for layer in model.layers:
        layer.structural_attention.beta.data.zero_()
    zero = model(ids,mask,relations)['logits']
    torch.testing.assert_close(empty,zero,atol=1e-6,rtol=1e-5)


def test_exact_optimizer_step_budget():
    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.logit = torch.nn.Parameter(torch.tensor(0.0))

        def forward(self, input_ids, attention_mask, relation_masks, special_tokens_mask=None):
            return {'logits': self.logit.expand(input_ids.shape[0])}

    model = Tiny()
    trainer = Trainer(model, torch.optim.SGD(model.parameters(), lr=.1), accumulation_steps=2)
    batch = {'input_ids':torch.zeros(1,2,dtype=torch.long),
             'attention_mask':torch.ones(1,2,dtype=torch.bool),
             'relation_masks':torch.zeros(1,2,2,2,dtype=torch.bool),
             'special_tokens_mask':torch.zeros(1,2,dtype=torch.bool),
             'labels':torch.ones(1)}
    result = trainer.train_epoch([batch]*10,{0:1.,1:1.},max_optimizer_steps=2)
    assert result['optimizer_steps'] == 2
    assert result['microbatches'] == 4
    assert model.logit.item() > 0
