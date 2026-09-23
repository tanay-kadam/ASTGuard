from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Sequence


METRIC_VERSION = "1.0"


def _validate(labels: Sequence[int], scores: Sequence[float]) -> None:
    if len(labels) != len(scores) or not labels:
        raise ValueError("labels and scores must be non-empty and have equal length")
    if any(y not in (0, 1) for y in labels):
        raise ValueError("labels must be binary")
    if any(not math.isfinite(float(s)) for s in scores):
        raise ValueError("scores must be finite")


def average_precision(labels: Sequence[int], scores: Sequence[float]) -> float | None:
    """Non-interpolated AP with tied scores grouped, matching sklearn semantics."""
    _validate(labels, scores)
    positives = sum(labels)
    if positives == 0 or positives == len(labels):
        return None
    order = sorted(range(len(labels)), key=lambda i: (-scores[i], i))
    tp = fp = 0
    total = 0.0
    previous_recall = 0.0
    cursor = 0
    while cursor < len(order):
        score = scores[order[cursor]]
        end = cursor
        while end < len(order) and scores[order[end]] == score:
            y = labels[order[end]]
            tp += y
            fp += 1 - y
            end += 1
        recall = tp / positives
        precision = tp / (tp + fp)
        total += (recall - previous_recall) * precision
        previous_recall = recall
        cursor = end
    return total


def roc_auc(labels: Sequence[int], scores: Sequence[float]) -> float | None:
    _validate(labels, scores)
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    wins, negatives_below = 0.0, 0
    ordered = sorted(zip(scores, labels))
    from itertools import groupby
    for _, group in groupby(ordered, key=lambda row: row[0]):
        tied = list(group)
        pos = sum(y for _, y in tied)
        neg = len(tied) - pos
        wins += pos * (negatives_below + .5 * neg)
        negatives_below += neg
    return wins / (positives * negatives)


def confusion(labels: Sequence[int], decisions: Sequence[bool]) -> dict[str, int]:
    if len(labels) != len(decisions):
        raise ValueError("labels and decisions differ in length")
    counts = Counter((int(y), int(bool(d))) for y, d in zip(labels, decisions))
    return {"tn": counts[(0, 0)], "fp": counts[(0, 1)], "fn": counts[(1, 0)], "tp": counts[(1, 1)]}


def threshold_metrics(labels: Sequence[int], decisions: Sequence[bool]) -> dict[str, float | int | bool | None]:
    c = confusion(labels, decisions)
    tn, fp, fn, tp = c["tn"], c["fp"], c["fn"], c["tp"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    f1 = 2 * precision * recall / (precision + recall) if recall is not None and precision + recall else 0.0
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn - fp * fn) / denominator) if denominator else None
    return c | {
        "accuracy": (tp + tn) / len(labels) if labels else None,
        "precision": precision, "recall": recall, "f1": f1, "mcc": mcc,
        "fpr": fp / (fp + tn) if fp + tn else None,
        "fnr": fn / (fn + tp) if fn + tp else None,
        "no_positive_predictions": tp + fp == 0,
    }


def evaluate_scores(labels: Sequence[int], scores: Sequence[float], threshold: float = 0.5) -> dict:
    _validate(labels, scores)
    result = {
        "metric_version": METRIC_VERSION,
        "count": len(labels), "positive_count": sum(labels), "negative_count": len(labels) - sum(labels),
        "average_precision": average_precision(labels, scores), "roc_auc": roc_auc(labels, scores),
        "threshold": encode_threshold(threshold),
    }
    return result | threshold_metrics(labels, [score >= threshold for score in scores])


def encode_threshold(value: float) -> float | str:
    return "+infinity" if math.isinf(value) and value > 0 else value


def decode_threshold(value: float | str) -> float:
    if value == "+infinity":
        return math.inf
    return float(value)


def official_vds_oracle(labels, scores, target_fpr=.005):
    _validate(labels,scores)
    if len(set(labels)) < 2:
        return {'official_vds_oracle':None,'oracle_diagnostics':{'reason':'missing_class'}}
    import numpy as np
    from sklearn.metrics import roc_curve
    fpr,tpr,thresholds=roc_curve(labels,scores)
    valid=np.where(fpr<=target_fpr)[0]
    index=valid[-1] if len(valid) else np.abs(fpr-target_fpr).argmin()
    return {'official_vds_oracle':float(1-tpr[index]),'oracle_diagnostics':{'threshold':encode_threshold(float(thresholds[index])),'fpr':float(fpr[index])}}
