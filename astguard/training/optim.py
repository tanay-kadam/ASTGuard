from __future__ import annotations


def build_adamw(model, *, pretrained_lr: float, new_multiplier: float, weight_decay: float, betas=(.9, .999), epsilon=1e-8):
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("optimizer construction requires PyTorch") from exc
    groups: dict[tuple[float, float], list] = {}
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        is_new = name.startswith("classifier") or any(part in name for part in ('.gate.', '.linear.', '.adapter.')) or name.endswith('.beta')
        lr = pretrained_lr * (new_multiplier if is_new else 1.0)
        no_decay = name.endswith("bias") or "LayerNorm" in name or "layer_norm" in name or name.endswith("beta")
        key = (lr, 0.0 if no_decay else weight_decay)
        groups.setdefault(key, []).append(parameter)
    return torch.optim.AdamW([{"params": params, "lr": lr, "weight_decay": decay} for (lr, decay), params in groups.items()], betas=betas, eps=epsilon)
