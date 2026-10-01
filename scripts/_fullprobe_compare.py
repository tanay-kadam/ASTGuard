import json
import statistics as st
from pathlib import Path

BASE = Path("artifacts/audits/diagnostics")

FILES = {
    "400step_fixed": BASE / "stage0_ast_dfg_fixed_trained.json",
    "400step_astguard": BASE / "stage0_astguard_trained.json",
    "fullprobe_fixed": BASE / "fullprobe_ast_dfg_fixed_trained.json",
    "fullprobe_astguard": BASE / "fullprobe_astguard_trained.json",
}


def agg_empty_graph(batches):
    mads = [b["mean_abs_logit_delta"] for b in batches]
    maxs = [b["max_abs_logit_delta"] for b in batches]
    fracs = [b["fraction_examples_with_nonzero_edges"] for b in batches]
    spearmans = [b["spearman_real_vs_empty"] for b in batches if b.get("spearman_real_vs_empty") is not None]
    ns = [b["n"] for b in batches]
    return {
        "mean_abs_logit_delta_mean": st.mean(mads) if mads else None,
        "max_abs_logit_delta_max": max(maxs) if maxs else None,
        "fraction_nonzero_edges_mean": st.mean(fracs) if fracs else None,
        "spearman_mean": st.mean(spearmans) if spearmans else None,
        "total_n": sum(ns),
    }


def agg_gradient_reach(batches):
    losses = [b["loss"] for b in batches if b.get("loss") is not None]
    per_layer = {}
    for b in batches:
        for layer, stats in b.get("per_layer", {}).items():
            per_layer.setdefault(layer, {"beta_grad_norm": [], "gate_grad_norm": []})
            if stats.get("beta_grad_norm") is not None:
                per_layer[layer]["beta_grad_norm"].append(stats["beta_grad_norm"])
            if stats.get("gate_grad_norm") is not None:
                per_layer[layer]["gate_grad_norm"].append(stats["gate_grad_norm"])
    per_layer_summary = {}
    for layer, vals in per_layer.items():
        per_layer_summary[layer] = {
            "beta_grad_norm_mean": st.mean(vals["beta_grad_norm"]) if vals["beta_grad_norm"] else None,
            "gate_grad_norm_mean": st.mean(vals["gate_grad_norm"]) if vals["gate_grad_norm"] else None,
        }
    return {
        "loss_mean": st.mean(losses) if losses else None,
        "per_layer": per_layer_summary,
    }


def agg_gate_values(batches):
    per_layer = {}
    for b in batches:
        for layer, stats in b.items():
            per_layer.setdefault(layer, {"mean": [], "std": []})
            if "mean" in stats:
                per_layer[layer]["mean"].append(stats["mean"])
            if "std" in stats:
                per_layer[layer]["std"].append(stats["std"])
    out = {}
    for layer, vals in per_layer.items():
        out[layer] = {
            "mean_of_means": st.mean(vals["mean"]) if vals["mean"] else None,
            "mean_of_stds": st.mean(vals["std"]) if vals["std"] else None,
        }
    return out


summary = {}
for label, path in FILES.items():
    if not path.exists():
        summary[label] = {"error": "missing"}
        continue
    data = json.loads(path.read_text())
    summary[label] = {
        "variant": data.get("variant"),
        "n_batches": data.get("n_batches"),
        "n_examples": data.get("n_examples"),
        "n_positive": data.get("n_positive"),
        "empty_graph_sensitivity": agg_empty_graph(data.get("empty_graph_sensitivity", [])),
        "gradient_reach": agg_gradient_reach(data.get("gradient_reach", [])),
        "gate_values": agg_gate_values(data.get("gate_values", [])) if data.get("gate_values") else {},
    }

print(json.dumps(summary, indent=2))
