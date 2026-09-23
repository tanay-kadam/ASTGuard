"""Measure warmed training-step cost for a resolved model on real cached features."""
from __future__ import annotations

import argparse
import dataclasses
import json
import statistics
import sys
import time
from itertools import cycle
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.config import load_config
from astguard.data.schema import read_jsonl
from astguard.models.factory import create_collator, create_model
from astguard.training.engine import weighted_bce_logits
from astguard.training.optim import build_adamw
from astguard.training.seeds import set_seed
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import object_hash


def _synchronize(torch, device: str) -> None:
    if device.startswith("cuda"):
        torch.cuda.synchronize()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--features", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--warmup-steps", type=int, default=10)
    parser.add_argument("--measured-steps", type=int, default=100)
    parser.add_argument("--allow-cpu", action="store_true")
    args = parser.parse_args(argv)
    if args.warmup_steps < 0 or args.measured_steps <= 0:
        raise ValueError("step counts must be nonnegative/positive")

    import torch
    from torch.utils.data import DataLoader

    config = load_config(args.config)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu" and not args.allow_cpu:
        raise RuntimeError("GPU benchmark requested but CUDA is unavailable; pass --allow-cpu only for plumbing checks")
    set_seed(config.training.seed)
    rows = list(read_jsonl(args.features))
    if not rows:
        raise ValueError("benchmark feature file is empty")
    labels = [int(row["label"]) for row in rows]
    positives, negatives = sum(labels), len(labels) - sum(labels)
    if not positives or not negatives:
        raise ValueError("benchmark features require both classes")
    batches = list(DataLoader(rows, batch_size=config.training.microbatch_size, shuffle=False,
                              collate_fn=create_collator(config, training=True)))
    iterator = cycle(batches)
    model = create_model(config).to(device).train()
    optimizer = build_adamw(model, pretrained_lr=config.training.pretrained_lr,
                            new_multiplier=config.training.new_module_lr_multiplier,
                            weight_decay=config.training.weight_decay,
                            betas=config.training.adam_betas, epsilon=config.training.adam_epsilon)
    weights = {0: len(labels) / (2 * negatives), 1: len(labels) / (2 * positives)}
    if config.training.loss == "unweighted_bce":
        weights = {0: 1.0, 1: 1.0}
    use_autocast = device == "cuda" and config.training.precision != "fp32"
    dtype = torch.bfloat16 if use_autocast and torch.cuda.is_bf16_supported() else torch.float16
    scaler = torch.amp.GradScaler("cuda", enabled=use_autocast and dtype == torch.float16)

    def optimizer_step() -> int:
        optimizer.zero_grad(set_to_none=True)
        examples = 0
        for _ in range(config.training.gradient_accumulation):
            batch = next(iterator)
            batch_size = len(batch["labels"])
            examples += batch_size
            with torch.autocast(device_type=device, dtype=dtype, enabled=use_autocast):
                if "graph_attention_mask" in batch:
                    outputs = model(**{key: batch[key].to(device) for key in
                                       ("input_ids", "position_ids", "graph_attention_mask")})
                elif "relation_masks" not in batch:
                    outputs = model(batch["input_ids"].to(device),batch["attention_mask"].to(device))
                else:
                    outputs = model(batch["input_ids"].to(device), batch["attention_mask"].to(device),
                                    batch["relation_masks"].to(device),
                                    special_tokens_mask=batch["special_tokens_mask"].to(device))
                loss = weighted_bce_logits(outputs["logits"].float(), batch["labels"].to(device), weights)
            scaler.scale(loss / config.training.gradient_accumulation).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.training.grad_clip_norm, error_if_nonfinite=True)
        scaler.step(optimizer)
        scaler.update()
        return examples

    for _ in range(args.warmup_steps):
        optimizer_step()
    _synchronize(torch, device)
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    durations, examples = [], 0
    for _ in range(args.measured_steps):
        start = time.perf_counter()
        count = optimizer_step()
        _synchronize(torch, device)
        durations.append(time.perf_counter() - start)
        examples += count
    total = sum(durations)
    cuda = None
    if device == "cuda":
        properties = torch.cuda.get_device_properties(0)
        allocated, reserved = torch.cuda.max_memory_allocated(), torch.cuda.max_memory_reserved()
        cuda = {"name": properties.name, "total_memory_bytes": properties.total_memory,
                "peak_allocated_bytes": allocated, "peak_reserved_bytes": reserved,
                "headroom_bytes": properties.total_memory - reserved,
                "four_gib_headroom_met": properties.total_memory - reserved >= 4 * 1024**3,
                "bf16_supported": torch.cuda.is_bf16_supported()}
    rss = None
    try:
        import psutil
        rss = psutil.Process().memory_info().rss
    except ImportError:
        pass
    result = {"schema_version": "training-benchmark-v1", "model_id": config.model.variant,
              "config_hash": object_hash(dataclasses.asdict(config)), "device": device,
              "precision": config.training.precision, "microbatch_size": config.training.microbatch_size,
              "gradient_accumulation": config.training.gradient_accumulation,
              "effective_batch_size": config.training.effective_batch_size,
              "sequence_length_max": max(len(row["input_ids"]) for row in rows),
              "warmup_steps": args.warmup_steps, "measured_steps": args.measured_steps,
              "examples": examples, "seconds_total": total,
              "steps_per_second": args.measured_steps / total,
              "examples_per_second": examples / total,
              "step_seconds_mean": statistics.mean(durations),
              "step_seconds_median": statistics.median(durations),
              "step_seconds_p95": sorted(durations)[min(len(durations)-1, int(.95 * len(durations)))],
              "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
              "cpu_rss_bytes": rss, "cuda": cuda, "scientific_result": False}
    atomic_write_json(args.output, result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
