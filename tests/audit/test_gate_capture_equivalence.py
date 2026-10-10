import torch
from tests.unit.test_neural import setup_model,inputs


def test_gate_diagnostics_do_not_change_logits():
    model,_=setup_model(beta=1.)
    ids,mask,relations,specials=inputs()
    with torch.no_grad():
        before=model(ids,mask,relations,special_tokens_mask=specials)['logits']
        after=model(ids,mask,relations,special_tokens_mask=specials,output_attentions=True)['logits']
    torch.testing.assert_close(before,after,atol=0,rtol=0)
    assert all(layer.structural_attention.last_diagnostics['gates'] is not None for layer in model.layers)
