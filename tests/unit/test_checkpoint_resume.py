import random
import uuid
from pathlib import Path

import numpy as np
import pytest
import torch

from astguard.training.checkpoint import load_resume_checkpoint,save_resume_checkpoint


def _step(model,optimizer):
    optimizer.zero_grad(set_to_none=True)
    inputs=torch.rand(4,3)
    loss=model(inputs).square().mean()
    loss.backward();optimizer.step()


def test_optimizer_boundary_resume_is_exact_and_config_guarded():
    path=Path(__file__).resolve().parents[2]/"artifacts"/"test"/("resume-"+uuid.uuid4().hex+".pt")
    random.seed(7);np.random.seed(7);torch.manual_seed(7)
    uninterrupted=torch.nn.Linear(3,2)
    optimizer=torch.optim.AdamW(uninterrupted.parameters(),lr=.01)
    _step(uninterrupted,optimizer)
    save_resume_checkpoint(path,model=uninterrupted,optimizer=optimizer,scheduler=None,scaler=None,
                           epoch=1,step=1,best_metric=.2,config_hash="config")
    _step(uninterrupted,optimizer)
    expected={name:value.detach().clone() for name,value in uninterrupted.state_dict().items()}

    resumed=torch.nn.Linear(3,2)
    resumed_optimizer=torch.optim.AdamW(resumed.parameters(),lr=.01)
    state=load_resume_checkpoint(path,model=resumed,optimizer=resumed_optimizer,expected_config_hash="config")
    assert state["epoch"]==1 and state["step"]==1
    _step(resumed,resumed_optimizer)
    assert all(torch.equal(expected[name],value) for name,value in resumed.state_dict().items())

    with pytest.raises(ValueError,match="config mismatch"):
        load_resume_checkpoint(path,model=resumed,expected_config_hash="different")
