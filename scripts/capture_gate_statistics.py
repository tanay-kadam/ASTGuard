"""Stream E9 gate/effective-coefficient/edge-mass statistics from a fitted run."""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from astguard.config import load_config
from astguard.data.schema import read_jsonl
from astguard.models.factory import create_collator, create_model
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import hash_uniform, object_hash, sha256_file


class Accumulator:
    def __init__(self, bins=10000):
        self.bins = bins; self.count = self.zero_degree = self.below = self.above = 0
        self.total = self.squares = self.minimum = self.maximum = None
        self.histogram = [0] * bins

    def add(self, values, eligible):
        import torch
        self.zero_degree += int((~eligible).sum())
        values = values[eligible].float().cpu()
        if not len(values): return
        self.count += len(values); value_sum = float(values.sum()); square_sum = float((values*values).sum())
        self.total = value_sum if self.total is None else self.total + value_sum
        self.squares = square_sum if self.squares is None else self.squares + square_sum
        low, high = float(values.min()), float(values.max())
        self.minimum = low if self.minimum is None else min(self.minimum, low)
        self.maximum = high if self.maximum is None else max(self.maximum, high)
        self.below += int((values < .05).sum()); self.above += int((values > .95).sum())
        counts = torch.bincount((values.clamp(0, 1)*(self.bins-1)).long(), minlength=self.bins).tolist()
        self.histogram = [left + right for left, right in zip(self.histogram, counts)]

    def report(self):
        if not self.count:
            return {"eligible_count": 0, "zero_degree_count": self.zero_degree, "mean": None, "median": None,
                    "std": None, "minimum": None, "maximum": None, "below_0.05": None, "above_0.95": None}
        target = (self.count-1)//2; cumulative = 0; median_bin = 0
        for index, count in enumerate(self.histogram):
            cumulative += count
            if cumulative > target: median_bin = index; break
        mean = self.total/self.count
        return {"eligible_count": self.count, "zero_degree_count": self.zero_degree, "mean": mean,
                "median": median_bin/(self.bins-1), "median_method": f"{self.bins}-bin bounded histogram",
                "std": math.sqrt(max(0., self.squares/self.count-mean*mean)), "minimum": self.minimum,
                "maximum": self.maximum, "below_0.05": self.below/self.count, "above_0.95": self.above/self.count}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True); parser.add_argument("--features", required=True)
    parser.add_argument("--role", default="test"); parser.add_argument("--detail-count", type=int, default=2000)
    parser.add_argument("--output-dir"); args = parser.parse_args(argv)
    import pyarrow as pa
    import pyarrow.parquet as pq
    import torch
    from safetensors.torch import load_model
    from torch.utils.data import DataLoader

    run = Path(args.run); output = Path(args.output_dir or run/"analysis"/"gates"); output.mkdir(parents=True, exist_ok=True)
    config = load_config(run/"config.resolved.yaml"); config_hash = object_hash(dataclasses.asdict(config))
    if config.model.variant not in {"astguard", "astguard_ast_only", "astguard_dfg_only", "astguard_dropout"}:
        raise ValueError("E9 gate capture requires an adaptive gate model")
    if args.role == "test":
        from astguard.protocol import verify_test_lock
        verify_test_lock(run_config=config_hash)
    rows = [row for row in read_jsonl(args.features) if row.get("role") == args.role]
    detailed = {row["sample_id"] for row in sorted(rows, key=lambda row: hash_uniform("e9-detail-v1", row["sample_id"]))[:args.detail_count]}
    checkpoint = run/"checkpoints"/"best.safetensors"; model = create_model(config); load_model(model, str(checkpoint))
    device = "cuda" if torch.cuda.is_available() else "cpu"; model.to(device).eval()
    loader = DataLoader(rows, batch_size=config.training.microbatch_size, shuffle=False, collate_fn=create_collator(config, False))
    stats = defaultdict(Accumulator); mass_stats = defaultdict(Accumulator); writer = None
    relations = list(model.relations)
    with torch.no_grad():
        for batch in loader:
            masks = batch["relation_masks"].to(device)
            relation_index = {name: i for i, name in enumerate(("ast", "dfg"))}
            selected_masks = masks[:, [relation_index[name] for name in relations]]
            result = model(batch["input_ids"].to(device), batch["attention_mask"].to(device), masks,
                           special_tokens_mask=batch["special_tokens_mask"].to(device), output_attentions=True)
            detail_rows = []
            for layer_index, (layer, attention_probs) in enumerate(zip(model.layers, result["attentions"])):
                attention = layer.structural_attention
                if attention is None or attention.last_diagnostics is None: continue
                gates = attention.last_diagnostics["gates"]
                degrees = selected_masks.sum(-1)
                for relation, relation_name in enumerate(relations):
                    edge_mass = (attention_probs * selected_masks[:, relation, None]).sum(-1)
                    for head in range(gates.shape[1]):
                        eligible = degrees[:, relation] > 0
                        key = (layer_index, head, relation_name)
                        stats[key].add(gates[:, head, :, relation], eligible)
                        mass_stats[key].add(edge_mass[:, head], eligible)
                        beta = float(attention.beta[head, relation].detach().cpu())
                        for batch_index, sample_id in enumerate(batch["sample_ids"]):
                            if sample_id not in detailed: continue
                            indices = torch.where(eligible[batch_index])[0].tolist()
                            for query in indices:
                                gate = float(gates[batch_index, head, query, relation].cpu())
                                detail_rows.append({"sample_id": sample_id, "layer": layer_index, "head": head,
                                                    "query": query, "relation": relation_name,
                                                    "degree": int(degrees[batch_index, relation, query]),
                                                    "gate": gate, "beta": beta, "effective_coefficient": beta*gate,
                                                    "pre_dropout_edge_mass": float(edge_mass[batch_index, head, query].cpu())})
            if detail_rows:
                table = pa.Table.from_pylist(detail_rows)
                if writer is None: writer = pq.ParquetWriter(output/"detailed.parquet", table.schema)
                writer.write_table(table)
    if writer is not None: writer.close()
    summary = []
    for key in sorted(stats):
        layer, head, relation = key
        attention = model.layers[layer].structural_attention
        relation_position = relations.index(relation); beta = float(attention.beta[head, relation_position].detach().cpu())
        gate = stats[key].report(); mass = mass_stats[key].report()
        summary.append({"layer": layer, "head": head, "relation": relation, "beta": beta,
                        "effective_coefficient_mean": None if gate["mean"] is None else beta*gate["mean"],
                        "gate": gate, "pre_dropout_edge_mass": mass})
    report = {"schema_version": "gate-statistics-v1", "run_id": run.name, "role": args.role,
              "checkpoint_sha256": sha256_file(checkpoint), "feature_sha256": sha256_file(args.features),
              "detail_namespace": "e9-detail-v1", "detail_sample_count": len(detailed), "statistics": summary}
    atomic_write_json(output/"gate_statistics.json", report)
    print(output/"gate_statistics.json")
    return 0


if __name__ == "__main__": raise SystemExit(main())
