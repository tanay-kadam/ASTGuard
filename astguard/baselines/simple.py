from __future__ import annotations

import json
import math
import random
from pathlib import Path

from astguard.parsing.lexical import lex
from astguard.utils.atomic_io import atomic_write_json


class PriorBaseline:
    def __init__(self):
        self.prevalence: float | None = None

    def fit(self, rows: list[dict]) -> None:
        if not rows:
            raise ValueError("empty training set")
        self.prevalence = sum(int(row["label"]) for row in rows) / len(rows)

    def predict_logit(self, row: dict) -> float:
        if self.prevalence is None:
            raise RuntimeError("model is not fitted")
        value = min(max(self.prevalence, 1e-12), 1 - 1e-12)
        return math.log(value / (1 - value))


class HashedLogisticBaseline:
    """Dependency-free hashed logistic model used only by the smoke pipeline."""

    def __init__(self, dimensions: int = 256, seed: int = 42, include_structure: bool = False, adaptive: bool = False):
        self.dimensions = dimensions
        self.seed = seed
        self.include_structure = include_structure
        self.adaptive = adaptive
        self.weights = [0.0] * (dimensions + 3)

    def vectorize(self, row: dict) -> dict[int, float]:
        source = row.get("source_canonical", "")
        values: dict[int, float] = {}
        for token in lex(source):
            index = sum(token.text.encode("utf-8")) % self.dimensions
            values[index] = values.get(index, 0.0) + 1.0
        scale = max(1.0, sum(values.values()))
        values = {index: value / scale for index, value in values.items()}
        values[self.dimensions] = 1.0
        if self.include_structure:
            ast_count = float(row.get("ast_edge_count", len(row.get("ast_token_edges", []))))
            dfg_count = float(row.get("dfg_edge_count", len(row.get("dfg_token_edges", []))))
            values[self.dimensions + 1] = math.log1p(ast_count) / 10
            values[self.dimensions + 2] = math.log1p(dfg_count) / 10
            if self.adaptive:
                lexical_count = max(1, len(lex(source)))
                values[self.dimensions + 1] *= min(1.0, lexical_count / 20)
                values[self.dimensions + 2] *= min(1.0, lexical_count / 20)
        return values

    def predict_logit(self, row: dict) -> float:
        return sum(self.weights[index] * value for index, value in self.vectorize(row).items())

    def fit(self, rows: list[dict], epochs: int = 12, learning_rate: float = .5) -> list[dict]:
        labels = [int(row["label"]) for row in rows]
        positives, negatives = sum(labels), len(labels) - sum(labels)
        if positives == 0 or negatives == 0:
            raise ValueError("training requires both classes")
        class_weights = {1: len(labels) / (2 * positives), 0: len(labels) / (2 * negatives)}
        rng = random.Random(self.seed)
        history = []
        for epoch in range(epochs):
            order = list(range(len(rows)))
            rng.shuffle(order)
            loss = 0.0
            for index in order:
                row, label = rows[index], labels[index]
                vector = self.vectorize(row)
                logit = sum(self.weights[i] * value for i, value in vector.items())
                probability = 1 / (1 + math.exp(-max(-30, min(30, logit))))
                weight = class_weights[label]
                loss += weight * (math.log1p(math.exp(-logit)) if label else math.log1p(math.exp(logit)))
                gradient = weight * (probability - label)
                for i, value in vector.items():
                    self.weights[i] -= learning_rate * gradient * value
            history.append({"epoch": epoch + 1, "loss": loss / len(rows)})
        return history

    def save(self, path: str | Path) -> None:
        atomic_write_json(path, {"type": "plumbing_hashed_logistic", "dimensions": self.dimensions,
                                "seed": self.seed, "include_structure": self.include_structure,
                                "adaptive": self.adaptive, "weights": self.weights})

    @classmethod
    def load(cls, path: str | Path) -> "HashedLogisticBaseline":
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        model = cls(value["dimensions"], value["seed"], value["include_structure"], value["adaptive"])
        model.weights = [float(x) for x in value["weights"]]
        return model


class TfidfLogisticBaseline:
    """Registered classical baseline; vocabulary and IDF are fit on train only."""

    def __init__(self,tokenizer=None):
        self.pipeline = None
        self.selected_c = None
        self.tokenizer=tokenizer

    def _window(self,source: str) -> str:
        if self.tokenizer is not None:
            encoded=self.tokenizer.encode(source,max_length=512)
            boundary=max((end for start,end in encoded.offsets_byte if end),default=0)
            source=source.encode('utf-8')[:boundary].decode('utf-8','ignore')
        return " ".join(token.text for token in lex(source))

    def fit(self, train_rows: list[dict], tune_rows: list[dict], candidates=(.01,.1,1,10)) -> dict:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
        except ImportError as exc:
            raise RuntimeError("TF-IDF baseline requires scikit-learn") from exc
        from astguard.evaluation.metrics import average_precision
        train_x = [self._window(row["source_canonical"]) for row in train_rows]
        tune_x = [self._window(row["source_canonical"]) for row in tune_rows]
        train_y = [int(row["label"]) for row in train_rows]
        tune_y = [int(row["label"]) for row in tune_rows]
        vectorizer = TfidfVectorizer(token_pattern=r"[^ ]+", ngram_range=(1,2), max_features=100000, min_df=2, lowercase=False)
        matrix = vectorizer.fit_transform(train_x)
        tune_matrix = vectorizer.transform(tune_x)
        trials = []
        best = None
        for c in candidates:
            model = LogisticRegression(C=c,class_weight="balanced",max_iter=2000,random_state=42,solver="liblinear")
            model.fit(matrix,train_y)
            scores = model.predict_proba(tune_matrix)[:,1].tolist()
            ap = average_precision(tune_y,scores)
            trials.append({"C":c,"tune_average_precision":ap})
            key = (-1 if ap is None else ap, -c)
            if best is None or key > best[0]: best=(key,c,model)
        self.selected_c, model = best[1], best[2]
        self.pipeline=(vectorizer,model)
        return {"selected_C":self.selected_c,"trials":trials}

    def predict(self, rows: list[dict]) -> list[float]:
        if self.pipeline is None: raise RuntimeError("model is not fitted")
        vectorizer,model=self.pipeline
        matrix=vectorizer.transform([self._window(row["source_canonical"]) for row in rows])
        return model.predict_proba(matrix)[:,1].tolist()
