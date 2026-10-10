import torch
from tests.unit.test_neural import setup_model

def test_model_initialization_does_not_reseed_cuda(monkeypatch):
    calls=[]
    monkeypatch.setattr(torch.cuda,'manual_seed_all',calls.append)
    setup_model(beta=1.)
    assert calls == [17,42], calls
