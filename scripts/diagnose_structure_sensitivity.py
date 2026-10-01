"""Stage 0 diagnostic: can structural bias actually reach the prediction?

Development-only tool for the structure-usage study
(`docs/STRUCTURE_USAGE_PROTOCOL.md`). It answers three narrow questions on a
real (or freshly initialized) checkpoint, using real feature batches:

1. Do gradients from the task loss reach `beta` and the gate parameters at
   every active structural layer?
2. Does replacing `relation_masks` with an all-empty graph change the
   logits at all, and does it change the ranking of examples?
3. What do the learned gate values actually look like (mean/std/min/max),
   since a gate stuck near 0.5 for every input cannot have learned to
   discriminate structure.

This does not evaluate a model scientifically and is not a substitute for
`astguard.evaluate`. It is a fast sanity check to decide whether spending
compute on Stage 1 (the graph-intervention study) is worthwhile at all.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_batches(features_path, config, collator, max_examples, batch_size, seed):
    import torch
    from torch.utils.data import DataLoader

    from astguard.train import _FeatureDataset

    dataset = _FeatureDataset(
        features_path,
        role="tune",
        manifest_hash=config.dataset.manifest_hash,
        preprocessing_hash=config.preprocessing.cache_hash,
    )
    if len(dataset) == 0:
        raise ValueError("feature file has no tune-role rows")
    if max_examples and len(dataset) > max_examples:
        indices = list(range(max_examples))
        dataset = torch.utils.data.Subset(dataset, indices)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, collate_fn=collator)
    return loader


def _structural_layers(model):
    return [(index, layer.structural_attention) for index, layer in enumerate(model.layers)
            if layer.structural_attention is not None]


def gradient_reach_report(model, batch, class_weights, device):
    import torch
    from astguard.training.engine import weighted_bce_logits

    model.train()
    model.zero_grad(set_to_none=True)
    output = model(batch["input_ids"], batch["attention_mask"], batch.get("relation_masks"),
                   special_tokens_mask=batch.get("special_tokens_mask"))
    loss = weighted_bce_logits(output["logits"], batch["labels"], class_weights)
    loss.backward()
    per_layer = {}
    for index, attention in _structural_layers(model):
        entry = {}
        if attention.beta is not None:
            grad = attention.beta.grad
            entry["beta_grad_norm"] = float(grad.norm().item()) if grad is not None else None
            entry["beta_grad_finite"] = bool(torch.isfinite(grad).all().item()) if grad is not None else None
        if attention.gate is not None:
            gate_grads = [p.grad for p in attention.gate.parameters() if p.grad is not None]
            if gate_grads:
                total_norm = float(sum(g.norm() ** 2 for g in gate_grads).sqrt().item())
                entry["gate_grad_norm"] = total_norm
                entry["gate_grad_finite"] = bool(all(torch.isfinite(g).all().item() for g in gate_grads))
            else:
                entry["gate_grad_norm"] = None
                entry["gate_grad_finite"] = None
        per_layer[str(index)] = entry
    model.zero_grad(set_to_none=True)
    return {"loss": float(loss.item()), "per_layer": per_layer}


def empty_graph_report(model, batch, device):
    import torch

    model.eval()
    with torch.no_grad():
        real = model(batch["input_ids"], batch["attention_mask"], batch.get("relation_masks"),
                     special_tokens_mask=batch.get("special_tokens_mask"))["logits"]
        empty_masks = torch.zeros_like(batch["relation_masks"]) if batch.get("relation_masks") is not None else None
        empty = model(batch["input_ids"], batch["attention_mask"], empty_masks,
                      special_tokens_mask=batch.get("special_tokens_mask"))["logits"]
    real_cpu = real.detach().cpu()
    empty_cpu = empty.detach().cpu()
    abs_delta = (real_cpu - empty_cpu).abs()
    rank_changed = None
    if real_cpu.numel() >= 2:
        from scipy.stats import spearmanr

        correlation, _ = spearmanr(real_cpu.tolist(), empty_cpu.tolist())
        rank_changed = None if correlation != correlation else float(correlation)
    return {
        "mean_abs_logit_delta": float(abs_delta.mean().item()),
        "max_abs_logit_delta": float(abs_delta.max().item()),
        "fraction_examples_with_nonzero_edges": float((batch["relation_masks"].any(dim=(1, 2, 3))).float().mean().item())
        if batch.get("relation_masks") is not None else 0.0,
        "spearman_real_vs_empty": rank_changed,
        "n": int(real_cpu.numel()),
    }


def gate_value_report(model, batch):
    import torch

    model.eval()
    with torch.no_grad():
        model(batch["input_ids"], batch["attention_mask"], batch.get("relation_masks"),
              output_attentions=True, special_tokens_mask=batch.get("special_tokens_mask"))
    per_layer = {}
    for index, attention in _structural_layers(model):
        if attention.mode != "adaptive" or attention.last_diagnostics is None:
            continue
        gates = attention.last_diagnostics.get("gates")
        if gates is None:
            continue
        flat = gates.detach().float().flatten()
        per_layer[str(index)] = {
            "mean": float(flat.mean().item()),
            "std": float(flat.std().item()),
            "min": float(flat.min().item()),
            "max": float(flat.max().item()),
        }
    return per_layer


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--features", required=True, help="Tune-role feature JSONL joined to labels")
    parser.add_argument("--checkpoint", help="Optional best.safetensors to load before diagnosing")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-examples", type=int, default=256)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError("use a new output path; preserve previous diagnostic evidence")

    import torch

    from astguard.config import load_config
    from astguard.models.factory import create_collator, create_model

    config = load_config(args.config, allow_unresolved=True)
    model = create_model(config)
    if args.checkpoint:
        from safetensors.torch import load_model
        load_model(model, args.checkpoint)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    collator = create_collator(config, training=False)
    loader = _load_batches(args.features, config, collator, args.max_examples, args.batch_size, args.seed)

    batches = []
    for batch in loader:
        batch = {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}
        batches.append(batch)
    if not batches:
        raise ValueError("no batches produced from features file")

    positives = sum(int(b["labels"].sum().item()) for b in batches)
    total = sum(int(b["labels"].numel()) for b in batches)
    negatives = total - positives
    class_weights = {0: total / (2 * max(negatives, 1)), 1: total / (2 * max(positives, 1))}

    gradient_reports = [gradient_reach_report(model, batch, class_weights, device) for batch in batches]
    empty_graph_reports = [empty_graph_report(model, batch, device) for batch in batches]
    gate_reports = [gate_value_report(model, batch) for batch in batches]

    report = {
        "kind": "development_structure_sensitivity_diagnostic_not_model_evaluation",
        "config_path": str(Path(args.config).resolve()),
        "variant": config.model.variant,
        "structural_layers": list(config.model.structural_layers),
        "checkpoint": args.checkpoint,
        "device": device,
        "n_batches": len(batches),
        "n_examples": total,
        "n_positive": positives,
        "gradient_reach": gradient_reports,
        "empty_graph_sensitivity": empty_graph_reports,
        "gate_values": gate_reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({
        "variant": config.model.variant,
        "mean_abs_logit_delta_vs_empty": sum(r["mean_abs_logit_delta"] for r in empty_graph_reports) / len(empty_graph_reports),
        "gate_value_summary": gate_reports[0] if gate_reports else {},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
