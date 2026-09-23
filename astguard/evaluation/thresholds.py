from __future__ import annotations

import dataclasses
import math
from typing import Sequence

from astguard.evaluation.metrics import encode_threshold, threshold_metrics
from astguard.utils.hashing import ordered_ids_hash


@dataclasses.dataclass(frozen=True)
class ThresholdResult:
    threshold_id: str
    rule: str
    threshold: float | str
    calibration_id_hash: str
    calibration_count: int
    positive_count: int
    negative_count: int
    checkpoint_hash: str
    calibration_metrics: dict


class ThresholdSelector:
    def fit(
        self, sample_ids: Sequence[str], labels: Sequence[int], scores: Sequence[float],
        *, role: str, checkpoint_hash: str,
    ) -> dict[str, ThresholdResult]:
        if role != "cal":
            raise ValueError("threshold fitting is permitted only on role='cal'")
        if not (len(sample_ids) == len(labels) == len(scores)) or not labels:
            raise ValueError("calibration arrays must be non-empty and aligned")
        if len(set(sample_ids))!=len(sample_ids):
            raise ValueError('duplicate calibration IDs')
        from astguard.evaluation.metrics import _validate
        _validate(labels,scores)
        positives, negatives = sum(labels), len(labels) - sum(labels)
        if positives == 0 or negatives == 0:
            raise ValueError("calibration must contain both classes")
        candidates = [math.inf, *sorted(set(float(x) for x in scores), reverse=True)]
        rows = [(threshold, threshold_metrics(labels, [score >= threshold for score in scores])) for threshold in candidates]
        max_f1 = max(rows, key=lambda row: (row[1]["f1"], -(row[1]["fpr"] or 0), row[0]))
        eligible_fpr = [row for row in rows if row[1]["fpr"] is not None and row[1]["fpr"] <= .005]
        low_fpr = max(eligible_fpr, key=lambda row: (row[1]["recall"], -row[1]["fpr"], row[0]))
        eligible_recall = [row for row in rows if row[1]["recall"] is not None and row[1]["recall"] >= .80]
        recall80 = max(eligible_recall, key=lambda row: row[0])
        selections = {"max_f1": max_f1, "fpr_0.005": low_fpr, "recall_0.80": recall80}
        result: dict[str, ThresholdResult] = {}
        ids_hash = ordered_ids_hash(sample_ids)
        for name, (threshold, metrics) in selections.items():
            result[name] = ThresholdResult(
                threshold_id=f"{checkpoint_hash[:12]}:{name}:{ids_hash[:12]}", rule=name,
                threshold=encode_threshold(threshold), calibration_id_hash=ids_hash,
                calibration_count=len(labels), positive_count=positives, negative_count=negatives,
                checkpoint_hash=checkpoint_hash, calibration_metrics=metrics,
            )
        return result
