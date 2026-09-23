from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from astguard.analysis.gates import summarize_gates
from astguard.evaluation.metrics import average_precision, roc_auc, threshold_metrics
from astguard.evaluation.pairs import evaluate_pairs
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


def read_rows(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.suffix == ".parquet":
        import pyarrow.parquet as pq
        return pq.read_table(path).to_pylist()
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if not isinstance(value, list):
        raise ValueError(f"{path} must contain a JSON array, JSONL, or Parquet rows")
    return value


def pair_report(predictions: list[dict], pair_definitions: list[dict]) -> list[dict]:
    by_id = {row["sample_id"]: row for row in predictions}
    if len(by_id) != len(predictions):
        raise ValueError("duplicate prediction IDs")
    prepared, incomplete = [], 0
    for pair in pair_definitions:
        vulnerable = by_id.get(pair["vulnerable_id"])
        patched = by_id.get(pair["patched_id"])
        if vulnerable is None or patched is None:
            incomplete += 1
            continue
        prepared.append({"pair_id": pair["pair_id"], "vulnerable_score": vulnerable["probability"],
                         "patched_score": patched["probability"], "vulnerable_logit": vulnerable["logit"],
                         "patched_logit": patched["logit"], "vulnerable": vulnerable, "patched": patched})
    threshold_names = sorted(set.intersection(*[set(row.get("decisions", {})) for row in predictions])) if predictions else []
    reports = []
    for name in threshold_names:
        threshold_rows = []
        for row in prepared:
            item = dict(row)
            # evaluate_pairs accepts a numeric threshold; encoded decisions are authoritative,
            # so Boolean scores preserve >= semantics without reconstructing floating thresholds.
            item["vulnerable_score"] = float(row["vulnerable"]["decisions"][name])
            item["patched_score"] = float(row["patched"]["decisions"][name])
            threshold_rows.append(item)
        report = evaluate_pairs(threshold_rows, .5)
        report.update({"threshold_name": name, "incomplete_pair_count": incomplete})
        reports.append(report)
    # Pair ordering and margins do not depend on a threshold.
    ranking = evaluate_pairs(prepared, .5)
    reports.append({"threshold_name": "ranking_only", "pair_count": ranking["pair_count"],
                    "invalid_count": ranking["invalid_count"], "incomplete_pair_count": incomplete,
                    "pair_order": ranking["pair_order"], "mean_logit_margin": ranking["mean_logit_margin"]})
    return reports


def _length_bin(value: int) -> str:
    return "<=128" if value <= 128 else "129-256" if value <= 256 else "257-510" if value <= 510 else ">510"


def _degree_bin(value: float) -> str:
    return "0" if value == 0 else "1" if value == 1 else "2-4" if value <= 4 else "5-16" if value <= 16 else "17+"


def failure_strata(predictions: list[dict], features: list[dict]) -> list[dict]:
    by_id = {row["sample_id"]: row for row in features}
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for prediction in predictions:
        feature = by_id.get(prediction["sample_id"])
        if feature is None:
            raise ValueError(f"missing feature metadata for {prediction['sample_id']}")
        ast_nodes = max(1, len(feature.get("ast_leaf_to_bpe", {})))
        dfg_nodes = max(1, len(feature.get("leaf_to_bpe", {})))
        groups[("length", _length_bin(int(feature["original_bpe_length"])))].append(prediction)
        groups[("ast_status", feature.get("ast_status", "unknown"))].append(prediction)
        groups[("dfg_status", feature.get("dfg_status", "unknown"))].append(prediction)
        groups[("ast_degree", _degree_bin(len(feature.get("lexical_ast_edges", [])) / ast_nodes))].append(prediction)
        groups[("dfg_degree", _degree_bin(len(feature.get("lexical_dfg_edges", [])) / dfg_nodes))].append(prediction)
    result = []
    for (dimension, value), rows in sorted(groups.items()):
        labels = [int(row["label"]) for row in rows]
        scores = [float(row["probability"]) for row in rows]
        decisions = [bool(row.get("decisions", {}).get("max_f1", False)) for row in rows]
        positives, negatives = sum(labels), len(labels) - sum(labels)
        threshold = threshold_metrics(labels, decisions)
        result.append({"dimension": dimension, "stratum": value, "count": len(rows),
                       "positives": positives, "negatives": negatives,
                       "average_precision": average_precision(labels, scores), "roc_auc": roc_auc(labels, scores),
                       **threshold, "inferential_eligible": positives >= 30 and negatives >= 30})
    return result


def gate_report(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, tuple[list, list]] = defaultdict(lambda: ([], []))
    for row in rows:
        key = (row.get("layer"), row.get("head"), row.get("relation"))
        groups[key][0].append(float(row["gate"]))
        groups[key][1].append(float(row["degree"]))
    result = []
    for (layer, head, relation), (values, degrees) in sorted(groups.items()):
        summary = summarize_gates(values, degrees)
        result.append({"layer": layer, "head": head, "relation": relation, **summary})
    return result


def efficiency_report(paths: list[str | Path]) -> list[dict]:
    result = []
    for path in paths:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        result.append({"source": str(path), "source_sha256": sha256_file(path), **document})
    return result


def trapezoidal_area(points: list[tuple[float, float]]) -> dict:
    unique = {}
    for x, y in points:
        unique.setdefault(float(x), []).append(float(y))
    averaged = sorted((x, sum(values) / len(values)) for x, values in unique.items())
    if len(averaged) < 2:
        return {"area": None, "minimum_x": None, "maximum_x": None, "points": averaged}
    area = sum((right[0] - left[0]) * (left[1] + right[1]) / 2 for left, right in zip(averaged, averaged[1:]))
    return {"area": area, "minimum_x": averaged[0][0], "maximum_x": averaged[-1][0], "points": averaged}


def write_report(path: str | Path, value) -> None:
    atomic_write_json(path, value)

