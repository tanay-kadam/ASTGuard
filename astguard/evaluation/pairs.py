from __future__ import annotations

from typing import Iterable


def evaluate_pairs(rows: Iterable[dict], threshold: float) -> dict:
    valid = []
    invalid = 0
    for row in rows:
        if not {"pair_id", "vulnerable_score", "patched_score"}.issubset(row):
            invalid += 1
            continue
        valid.append(row)
    if not valid:
        return {"pair_count": 0, "invalid_count": invalid, "pair_order": None, "mean_logit_margin": None}
    order = outcomes = 0.0
    margins: list[float] = []
    counts = {"PC": 0, "PV": 0, "PB": 0, "PR": 0}
    for row in valid:
        vulnerable, patched = float(row["vulnerable_score"]), float(row["patched_score"])
        order += 1.0 if vulnerable > patched else 0.5 if vulnerable == patched else 0.0
        margins.append(float(row.get("vulnerable_logit", vulnerable)) - float(row.get("patched_logit", patched)))
        decision = (vulnerable >= threshold, patched >= threshold)
        key = {(True, False): "PC", (True, True): "PV", (False, False): "PB", (False, True): "PR"}[decision]
        counts[key] += 1
    n = len(valid)
    return {
        "pair_count": n, "invalid_count": invalid, "pair_order": order / n,
        "mean_logit_margin": sum(margins) / n,
        **{name: value / n for name, value in counts.items()},
    }

