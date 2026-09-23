"""Development-only feasibility checks for the proposed structural residual.

No model fitting, official-test access, or scientific performance claim. The graph
audit uses only the train role of the existing, deliberately tiny R2 pilot.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import statistics


def center(values):
    mean = statistics.mean(values)
    return [v - mean for v in values]


def logistic_loss(logit, label):
    return max(logit, 0.0) + math.log1p(math.exp(-abs(logit))) - label * logit


def mathematical_checks():
    # Exact uniform group average, including repeated graphs from automorphisms.
    graph = {(0, 1), (1, 2), (2, 3), (3, 0)}
    states = [0.2, -0.6, 0.7, 1.1]
    orbit = [{(p[a], p[b]) for a, b in graph}
             for p in itertools.permutations(range(4))]
    values = [math.tanh(sum(math.tanh(states[a] + 2 * states[b])
                            for a, b in g) / 4) for g in orbit]
    correction = center(values)
    assert abs(statistics.mean(correction)) < 1e-12
    # Any shared additive term cancels, even if it predicts labels very well.
    shifted = center([v + 13.25 for v in values])
    nuisance_error = max(abs(a - b) for a, b in zip(correction, shifted))
    assert nuisance_error < 1e-12
    assert center([1.7] * len(orbit)) == [0.0] * len(orbit)
    assert center([0.4]) == [0.0]
    z0 = 0.4
    p0 = 1 / (1 + math.exp(-z0))
    null_delta = statistics.mean(logistic_loss(z0 + c, p0)
                                 - logistic_loss(z0, p0) for c in correction)
    curvature_bound = statistics.mean(c * c for c in correction) / 8
    assert 0 < null_delta <= curvature_bound + 1e-12
    # Useful constructed alternative; probabilities are specified, not fitted.
    targets = [1 / (1 + math.exp(-(z0 + c))) for c in correction]
    useful_delta = statistics.mean(logistic_loss(z0 + c, y)
                                   - logistic_loss(z0, y)
                                   for c, y in zip(correction, targets))
    alignment = statistics.mean((y - p0) * c
                                for c, y in zip(correction, targets))
    assert -alignment - 1e-12 <= useful_delta <= -alignment + curvature_bound + 1e-12
    assert useful_delta < 0
    # Exhaustive K=2 reference sampling: Var(sample mean)=Var(response)/K.
    mu = statistics.mean(values)
    mc_mse = statistics.mean(((a + b) / 2 - mu) ** 2
                            for a, b in itertools.product(values, repeat=2))
    assert abs(mc_mse - statistics.pvariance(values) / 2) < 1e-12
    # Graph-dependent gating AFTER centering breaks centering.
    gated_mean = statistics.mean(c if c > 0 else 0 for c in correction)
    assert gated_mean > 0
    return dict(status="passed", kind="exact_finite_example_not_training",
                group_size=len(orbit), distinct_graphs=len({tuple(sorted(g)) for g in orbit}),
                additive_nuisance_cancellation_error=nuisance_error,
                null_bce_increase=null_delta, null_bce_upper_bound=curvature_bound,
                constructed_useful_bce_change=useful_delta,
                monte_carlo_k2_mse=mc_mse, post_center_gate_mean=gated_mean)


def visible_graph(feature, relation):
    mapping_name = "ast_leaf_to_bpe" if relation == "ast" else "leaf_to_bpe"
    mapping = {int(k): sorted(set(v)) for k, v in feature[mapping_name].items() if v}
    eligible = {i for i, (a, s) in enumerate(zip(feature["attention_mask"],
                                                feature["special_tokens_mask"])) if a and not s}
    mapping = {k: [i for i in v if i in eligible] for k, v in mapping.items()}
    mapping = {k: v for k, v in mapping.items() if v}
    edges = {(a, b) for a, b in feature[f"lexical_{relation}_edges"]
             if a in mapping and b in mapping and a != b}
    if relation == "ast":
        edges |= {(b, a) for a, b in edges}
    return mapping, edges


def null_draws(feature, relation, position_blocks, draws=16):
    mapping, edges = visible_graph(feature, relation)
    incoming = Counter(b for a, b in edges)
    outgoing = Counter(a for a, b in edges)
    ordered = sorted(mapping, key=lambda n: (min(mapping[n]), n))
    groups = defaultdict(list)
    block_of = {}
    for rank, node in enumerate(ordered):
        block = min(position_blocks - 1, position_blocks * rank // max(1, len(ordered)))
        block_of[node] = block
        groups[(incoming[node], outgoing[node], len(mapping[node]), block)].append(node)
    original_blocks = Counter((block_of[a], block_of[b]) for a, b in edges)
    seed_text = f"r3-null-audit|{feature['sample_id']}|{relation}|{position_blocks}"
    rng = random.Random(int(hashlib.sha256(seed_text.encode()).hexdigest()[:16], 16))
    variants = []
    changes = []
    for _ in range(draws):
        permutation = {}
        for group in groups.values():
            shuffled = rng.sample(group, len(group))
            permutation.update(zip(group, shuffled))
        changed = {(permutation[a], permutation[b]) for a, b in edges}
        assert Counter(b for a, b in changed) == incoming
        assert Counter(a for a, b in changed) == outgoing
        assert Counter((block_of[a], block_of[b]) for a, b in changed) == original_blocks
        assert all(a != b for a, b in changed)
        variants.append(tuple(sorted(changed)))
        changes.append(len(edges - changed) / len(edges) if edges else 0.0)
    return dict(nodes=len(mapping), directed_edges=len(edges),
                movable_nodes=sum(len(g) for g in groups.values() if len(g) > 1),
                distinct_draws=len(set(variants)),
                observed_any_change=any(c > 0 for c in changes),
                mean_edge_change=statistics.mean(changes))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path,
                        default=Path("runs/edge-pilot-20260923/features/train.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Use a new output path; preserve previous audit evidence")
    checks = mathematical_checks()
    raw = args.features.read_bytes()
    features = [json.loads(line) for line in raw.splitlines() if line]
    if not features or any(f.get("role") != "train" for f in features):
        raise ValueError("This feasibility audit only accepts nonempty train-role features")
    records = []
    for f in features:
        for relation in ("ast", "dfg"):
            for blocks in (1, 4):
                records.append(dict(sample_id=f["sample_id"], relation=relation,
                                    position_blocks=blocks,
                                    **null_draws(f, relation, blocks)))
    summaries = []
    for relation in ("ast", "dfg"):
        for blocks in (1, 4):
            selected = [r for r in records if r["relation"] == relation and r["position_blocks"] == blocks]
            nonempty = [r for r in selected if r["directed_edges"]]
            summaries.append(dict(relation=relation, position_blocks=blocks,
                                  functions=len(selected), nonempty_graphs=len(nonempty),
                                  functions_with_observed_change=sum(r["observed_any_change"] for r in selected),
                                  mean_edge_change_nonempty=statistics.mean(r["mean_edge_change"] for r in nonempty)
                                  if nonempty else None))
    report = dict(kind="development_null_feasibility_not_model_evaluation", mathematical_checks=checks,
                  source_path=args.features.as_posix(), source_sha256=hashlib.sha256(raw).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  labels_used=False, official_test_used=False, draws_per_condition=16,
                  limitations=["Tiny balanced R2 train cohort at length 64; not representative",
                               "No observed change in 16 draws does not prove a singleton orbit",
                               "Visible nodes of full-function extraction; not prefix-only extraction",
                               "Null graphs are feature interventions, not valid alternative programs"],
                  summary=summaries, records=records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"mathematical_checks": checks, "summary": summaries}, indent=2))


if __name__ == "__main__":
    main()
