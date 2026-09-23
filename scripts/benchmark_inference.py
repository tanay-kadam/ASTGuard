"""Registered E8 inference/transfer timing on a fixed hash-selected cohort."""
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
from astguard.training.seeds import set_seed
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import hash_uniform, object_hash, sha256_file


def _length_bin(value: int) -> int:
    return 0 if value <= 128 else 1 if value <= 256 else 2 if value <= 510 else 3


def _summary(values: list[float]) -> dict:
    ordered = sorted(values)
    return {"mean_seconds": statistics.mean(values), "median_seconds": statistics.median(values),
            "p95_seconds": ordered[min(len(ordered)-1, int(.95 * len(ordered)))], "raw_seconds": values}


def _move(batch, device):
    keys = ("input_ids", "position_ids", "graph_attention_mask") if "graph_attention_mask" in batch else (
        ("input_ids","attention_mask") if "relation_masks" not in batch else
        ("input_ids", "attention_mask", "relation_masks", "special_tokens_mask"))
    return {key: batch[key].to(device) for key in keys}


def _forward(model, batch):
    if "graph_attention_mask" in batch:
        return model(**batch)
    if "relation_masks" not in batch:
        return model(batch["input_ids"],batch["attention_mask"])
    return model(batch["input_ids"], batch["attention_mask"], batch["relation_masks"],
                 special_tokens_mask=batch["special_tokens_mask"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--features", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample-count", type=int, default=1000)
    parser.add_argument("--warmup-batches", type=int, default=50)
    parser.add_argument("--measured-batches", type=int, default=200)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--batch-sizes", type=int, nargs="+", default=[1, 16])
    parser.add_argument("--optimized-sequence", action="store_true",
                        help="use the SDPA backend; valid only for sequence_only practical timing")
    parser.add_argument("--allow-cpu", action="store_true")
    args = parser.parse_args(argv)
    import torch
    from safetensors.torch import load_model
    from torch.utils.data import DataLoader

    config = load_config(args.config)
    rows = list(read_jsonl(args.features))
    if not rows:
        raise ValueError("feature cohort is empty")
    roles = {row.get("role") for row in rows}
    if "test" in roles:
        from astguard.protocol import verify_test_lock
        verify_test_lock(run_config=object_hash(dataclasses.asdict(config)))
    per_bin = max(1, args.sample_count // 4)
    buckets = {index: [] for index in range(4)}
    for row in rows:
        buckets[_length_bin(int(row["original_bpe_length"]))].append(row)
    selected = []
    for index in range(4):
        selected.extend(sorted(buckets[index], key=lambda row: hash_uniform("e8-fixed-sample-v1", row["sample_id"]))[:per_bin])
    if len(selected) < args.sample_count:
        present = {row["sample_id"] for row in selected}
        remainder = sorted((row for row in rows if row["sample_id"] not in present),
                           key=lambda row: hash_uniform("e8-fixed-sample-v1", row["sample_id"]))
        selected.extend(remainder[:args.sample_count-len(selected)])
    if not selected:
        raise ValueError("no benchmark rows selected")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu" and not args.allow_cpu:
        raise RuntimeError("CUDA is required for E8; --allow-cpu is a plumbing-only override")
    set_seed(config.training.seed)
    if args.optimized_sequence:
        if config.model.variant!="sequence_only":
            raise ValueError("--optimized-sequence is valid only for sequence_only")
        from astguard.models.codebert import ASTGuardClassifier
        model=ASTGuardClassifier.from_pretrained(config.model.checkpoint,revision=config.model.revision,
            variant=config.model.variant,structural_layers=config.model.structural_layers,
            head_dropout=config.model.head_dropout,beta_init=config.model.beta_init,
            attn_implementation="sdpa")
    else:
        model = create_model(config)
    load_model(model, args.checkpoint)
    model.to(device).eval()
    results = []
    for batch_size in args.batch_sizes:
        loader = DataLoader(selected, batch_size=batch_size, shuffle=False, collate_fn=create_collator(config, False))
        iterator = cycle(loader)
        with torch.no_grad():
            for _ in range(args.warmup_batches):
                _forward(model, _move(next(iterator), device))
            if device == "cuda":
                torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
            for repeat in range(args.repeats):
                transfer_times, model_times, end_to_end_times = [], [], []
                examples = 0
                for _ in range(args.measured_batches):
                    batch = next(iterator)
                    examples += len(batch["labels"])
                    total_start = time.perf_counter()
                    start = time.perf_counter(); moved = _move(batch, device)
                    if device == "cuda": torch.cuda.synchronize()
                    transfer_times.append(time.perf_counter()-start)
                    start = time.perf_counter(); _forward(model, moved)
                    if device == "cuda": torch.cuda.synchronize()
                    model_times.append(time.perf_counter()-start)
                    end_to_end_times.append(time.perf_counter()-total_start)
                results.append({"batch_size": batch_size, "repeat": repeat, "examples": examples,
                                "model": _summary(model_times), "transfer": _summary(transfer_times),
                                "prepared_end_to_end": _summary(end_to_end_times),
                                "throughput_examples_per_second": examples/sum(end_to_end_times)})
    cuda = None
    if device == "cuda":
        cuda = {"peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
                "device": torch.cuda.get_device_name(0),
                "total_memory_bytes": torch.cuda.get_device_properties(0).total_memory}
    disk_bytes = Path(args.checkpoint).stat().st_size
    report = {"schema_version": "e8-inference-v1", "scientific_result": device == "cuda",
              "model_id": config.model.variant, "config_hash": object_hash(dataclasses.asdict(config)),
              "checkpoint_sha256": sha256_file(args.checkpoint), "feature_sha256": sha256_file(args.features),
              "sample_namespace": "e8-fixed-sample-v1", "sample_count": len(selected),
              "length_bin_counts": {str(key): sum(_length_bin(int(row["original_bpe_length"])) == key for row in selected) for key in range(4)},
              "label_independent_selection": True, "warmup_batches": args.warmup_batches,
              "measured_batches": args.measured_batches, "repeats": args.repeats,
              "backend": "sdpa" if args.optimized_sequence else "eager",
              "precision": config.training.precision, "device": device,
              "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
              "checkpoint_disk_bytes": disk_bytes, "cuda": cuda, "results": results}
    atomic_write_json(args.output, report)
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
