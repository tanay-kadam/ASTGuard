from __future__ import annotations

import math
from typing import Iterable


def sigmoid(logit: float) -> float:
    if logit >= 0:
        z = math.exp(-logit)
        return 1 / (1 + z)
    z = math.exp(logit)
    return z / (1 + z)


def predict_records(model, features: Iterable, *, run_id: str, model_id: str, seed: int) -> list[dict]:
    rows = []
    for feature in features:
        logit = float(model.predict_logit(feature))
        rows.append({"run_id": run_id, "sample_id": feature["sample_id"], "model_id": model_id,
                     "seed": seed, "logit": logit, "probability": sigmoid(logit)})
    return rows
