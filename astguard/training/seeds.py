from __future__ import annotations

import os
import random


def set_seed(seed: int, deterministic: bool = True) -> dict:
    random.seed(seed)
    state = {"python_seed": seed, "deterministic_requested": deterministic}
    try:
        import numpy as np
        np.random.seed(seed)
        state["numpy_seed"] = seed
    except ImportError:
        state["numpy_seed"] = None
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        if deterministic:
            torch.use_deterministic_algorithms(True, warn_only=True)
        state["torch_seed"] = seed
    except ImportError:
        state["torch_seed"] = None
    return state


def augmentation_seed(run_seed: int, epoch: int, sample_id: str, presentation: int) -> int:
    from astguard.utils.hashing import sha256_text
    return int(sha256_text(f"augmentation-v1|{run_seed}|{epoch}|{sample_id}|{presentation}")[:16], 16)

