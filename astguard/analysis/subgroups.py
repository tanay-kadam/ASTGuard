"""Pre-registered secondary parse-status subgroup analysis (protocol revision R1).

Subgroup membership comes only from the frozen, label-free feature status of
each test function. Results are descriptive: no p-values are produced, and
intervals are reported only for subgroups meeting the registered eligibility
rule (>=30 positives, >=30 negatives, adequate clusters).
"""
from __future__ import annotations

from collections import Counter

from astguard.evaluation.bootstrap import ClusterBootstrap
from astguard.evaluation.metrics import average_precision

SUBGROUPS = {
    "S_parsed": lambda feature: feature["ast_status"] == "ok",
    "S_failed": lambda feature: feature["ast_status"] != "ok",
    "S_dfg_supported": lambda feature: feature["dfg_status"] == "ok",
    "S_dfg_unsupported": lambda feature: feature["dfg_status"] != "ok",
}
INTERPRETATION_RULE = (
    "A gain concentrated in S_parsed is consistent with the structural mechanism. A comparable gain in S_failed, "
    "where no structural bias is applied, points to a non-structural source and weakens the mechanism claim. "
    "Subgroup results cannot replace or rescue a primary endpoint."
)
MIN_PER_CLASS = 30


def coverage_by_language(features: dict[str, dict], ids: list[str]) -> dict:
    totals, parsed, supported = Counter(), Counter(), Counter()
    for sample in ids:
        feature = features[sample]
        language = feature.get("language_selected", "unknown")
        totals[language] += 1
        parsed[language] += feature["ast_status"] == "ok"
        supported[language] += feature["dfg_status"] == "ok"
    return {language: {"count": totals[language], "ast_ok_fraction": parsed[language] / totals[language],
                       "dfg_ok_fraction": supported[language] / totals[language]} for language in sorted(totals)}


def subgroup_comparison(ids: list[str], features: dict[str, dict], left: dict[int, dict], right: dict[int, dict], *,
                        replicates: int = 10000, seed: int = 20260921) -> dict:
    seeds = sorted(set(left) & set(right))
    if len(seeds) < 2:
        raise ValueError("at least two paired training seeds are required")
    missing = [s for s in ids if s not in features]
    if missing:
        raise ValueError(f"missing feature rows for {len(missing)} predictions")
    report = {"paired_seeds": seeds, "population": len(ids),
              "coverage_by_language": coverage_by_language(features, ids), "subgroups": {}}
    for name, member in SUBGROUPS.items():
        subset = [s for s in ids if member(features[s])]
        labels = [int(left[seeds[0]][s]["label"]) for s in subset]
        components = [features[s]["component_id"] for s in subset]
        positives = sum(labels)
        entry = {"count": len(subset), "positives": positives, "negatives": len(subset) - positives,
                 "clusters": len(set(components))}
        left_scores = {k: [float(left[k][s]["probability"]) for s in subset] for k in seeds}
        right_scores = {k: [float(right[k][s]["probability"]) for s in subset] for k in seeds}
        per_seed = []
        for k in seeds:
            a, b = average_precision(labels, left_scores[k]), average_precision(labels, right_scores[k])
            per_seed.append({"seed": k, "left_ap": a, "right_ap": b,
                             "difference": None if a is None or b is None else a - b})
        differences = [row["difference"] for row in per_seed if row["difference"] is not None]
        entry["per_seed"] = per_seed
        entry["mean_difference"] = sum(differences) / len(differences) if len(differences) == len(seeds) else None
        eligible = positives >= MIN_PER_CLASS and entry["negatives"] >= MIN_PER_CLASS
        entry["hierarchical_interval_95"] = entry["seed_t_interval_95"] = None
        if eligible and entry["mean_difference"] is not None:
            result = ClusterBootstrap().hierarchical(labels, left_scores, right_scores, components,
                                                     replicates=replicates, seed=seed, confidence=.95)
            eligible = result["confirmatory_eligible"]
            if eligible:
                entry["hierarchical_interval_95"] = result["hierarchical_interval"]
                entry["seed_t_interval_95"] = result["seed_t_interval"]
            entry["invalid_replicates"] = result["invalid_replicates"]
        entry["inferential_eligible"] = bool(eligible)
        report["subgroups"][name] = entry
    return report
