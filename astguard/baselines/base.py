from __future__ import annotations

from abc import ABC,abstractmethod


class BaselineAdapter(ABC):
    """Minimal contract for models that do not share ASTGuard.forward."""

    @abstractmethod
    def prepare_features(self, rows):
        raise NotImplementedError

    @abstractmethod
    def fit(self, train_rows, tune_rows):
        raise NotImplementedError

    @abstractmethod
    def predict_to_common_schema(self, rows):
        raise NotImplementedError

    @abstractmethod
    def provenance(self):
        raise NotImplementedError

    @abstractmethod
    def status(self):
        raise NotImplementedError
