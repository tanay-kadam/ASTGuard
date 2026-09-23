"""Release-gate check: overfit a fixed balanced 32-example training fixture."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.config import load_config
from astguard.data.schema import read_jsonl
from astguard.models.factory import create_collator, create_model
from astguard.training.engine import Trainer
from astguard.training.optim import build_adamw
from astguard.training.seeds import set_seed
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import hash_uniform, object_hash


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--features", required=True, help="joined training-only features")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    import torch
    from torch.utils.data import DataLoader

    config = load_config(args.config)
    rows = [row for row in read_jsonl(args.features) if row.get("role") == "train"]
    selected = []
    for label in (0, 1):
        candidates = sorted((row for row in rows if int(row["label"]) == label),
                            key=lambda row: hash_uniform("baseline-overfit-v1", row["sample_id"]))
        selected.extend(candidates[:16])
    if len(selected) != 32 or sum(int(row["label"]) for row in selected) != 16:
        raise ValueError("balanced 16-positive/16-negative fixture cannot be constructed")
    set_seed(config.training.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = create_model(config).to(device)
    optimizer = build_adamw(model, pretrained_lr=config.training.pretrained_lr,
                            new_multiplier=config.training.new_module_lr_multiplier,
                            weight_decay=config.training.weight_decay,
                            betas=config.training.adam_betas, epsilon=config.training.adam_epsilon)
    loader = DataLoader(selected, batch_size=config.training.microbatch_size, shuffle=True,
                        collate_fn=create_collator(config, training=True),
                        generator=torch.Generator().manual_seed(config.training.seed))
    evaluation = DataLoader(selected, batch_size=config.training.microbatch_size, shuffle=False,
                            collate_fn=create_collator(config, training=False))
    trainer = Trainer(model, optimizer, grad_clip_norm=config.training.grad_clip_norm,
                      accumulation_steps=config.training.gradient_accumulation, device=device,
                      precision=config.training.precision)
    history = []
    while trainer.optimizer_steps < args.steps:
        log = trainer.train_epoch(loader, {0: 1.0, 1: 1.0}, max_optimizer_steps=args.steps)
        predictions = trainer.predict(evaluation)
        accuracy = sum((row["probability"] >= .5) == bool(row["label"]) for row in predictions) / len(predictions)
        history.append({"optimizer_steps": trainer.optimizer_steps, "accuracy": accuracy, "loss": log["loss"]})
        if accuracy >= .95:
            break
    accuracy = history[-1]["accuracy"]
    result = {"status": "passed" if accuracy >= .95 else "failed", "accuracy": accuracy,
              "required_accuracy": .95, "fixture_count": 32, "positive_count": 16,
              "optimizer_steps": trainer.optimizer_steps, "maximum_steps": args.steps,
              "model_id": config.model.variant, "config_hash": object_hash(dataclasses.asdict(config)),
              "sample_ids": [row["sample_id"] for row in selected], "device": device, "history": history}
    atomic_write_json(args.output, result)
    print(json.dumps({key: value for key, value in result.items() if key not in {"history", "sample_ids"}}, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
