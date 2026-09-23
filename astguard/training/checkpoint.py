from __future__ import annotations

import random
from pathlib import Path

from astguard.utils.hashing import object_hash


def save_resume_checkpoint(path, *, model, optimizer, scheduler, scaler, epoch, step, best_metric, config_hash, extra=None):
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("checkpointing requires PyTorch") from exc
    state = {
        'extra': extra or {},
        "model": model.state_dict(), "optimizer": optimizer.state_dict(),
        "scheduler": None if scheduler is None else scheduler.state_dict(),
        "scaler": None if scaler is None else scaler.state_dict(),
        "python_rng": random.getstate(), "torch_rng": torch.get_rng_state(),
        "cuda_rng": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        "epoch": epoch, "step": step, "best_metric": best_metric, "config_hash": config_hash,
    }
    import numpy as np
    state['numpy_rng'] = np.random.get_state()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    temporary = str(path) + '.partial'
    torch.save(state, temporary)
    import os
    os.replace(temporary, path)


def load_resume_checkpoint(path, *, model, optimizer=None, scheduler=None, scaler=None, expected_config_hash=None):
    import torch
    state = torch.load(path, map_location="cpu", weights_only=False)
    if expected_config_hash and state["config_hash"] != expected_config_hash:
        raise ValueError("checkpoint config mismatch")
    model.load_state_dict(state["model"])
    if optimizer is not None:
        optimizer.load_state_dict(state["optimizer"])
    if scheduler is not None and state["scheduler"] is not None:
        scheduler.load_state_dict(state["scheduler"])
    if scaler is not None and state["scaler"] is not None:
        scaler.load_state_dict(state["scaler"])
    random.setstate(state["python_rng"])
    import numpy as np
    np.random.set_state(state['numpy_rng'])
    torch.set_rng_state(state["torch_rng"])
    if torch.cuda.is_available() and state["cuda_rng"] is not None:
        torch.cuda.set_rng_state_all(state["cuda_rng"])
    return state
