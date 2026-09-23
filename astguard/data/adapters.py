from __future__ import annotations

import abc
from pathlib import Path
from typing import Iterable

from astguard.data.schema import SampleRecord, SchemaError, make_sample, read_jsonl


class DatasetAdapter(abc.ABC):
    @abc.abstractmethod
    def read(self, path: str | Path, release: str, split: str | None = None) -> tuple[list[SampleRecord], list[dict]]:
        raise NotImplementedError


class JsonlFunctionAdapter(DatasetAdapter):
    source_fields = ("func", "function", "code", "source", "source_code")
    label_fields = ("target", "label", "vulnerable", "is_vulnerable")
    id_fields = ("idx", "id", "function_id")

    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name

    @staticmethod
    def _first(row: dict, fields: Iterable[str]):
        for field in fields:
            if field in row:
                return row[field]
        return None

    def read(self, path: str | Path, release: str, split: str | None = None) -> tuple[list[SampleRecord], list[dict]]:
        records: list[SampleRecord] = []
        quarantine: list[dict] = []
        for index, row in enumerate(read_jsonl(path)):
            source = self._first(row, self.source_fields)
            label = self._first(row, self.label_fields)
            reason = None
            if not isinstance(source, str):
                reason = "missing_or_nonstring_source"
            if type(label) not in (int, bool) or label not in (0, 1):
                reason = reason or "invalid_label"
            if reason:
                from astguard.utils.hashing import object_hash
                quarantine.append({"row_index": index, "reason": reason, "original_id": self._first(row, self.id_fields), 'row_hash':object_hash(row)})
                continue
            original_id = self._first(row, self.id_fields)
            record_split = split or str(row.get("split", "unknown"))
            metadata = {
                "repository_url": row.get("repository_url") or row.get("repo"),
                "file_path": row.get("file_path") or row.get("file"),
                "commit_id": row.get("commit_id") or row.get("commit"),
                "timestamp": row.get("timestamp") or row.get("date"),
                "language_metadata": row.get("language"),
                "cwe_ids": _list(row.get("cwe_ids") or row.get("cwe")),
                "cve_ids": _list(row.get("cve_ids") or row.get("cve")),
                "pair_ids": _list(row.get("pair_ids") or row.get("pair_id")),
                # Both official PrimeVul and standalone DiverseVul call this
                # field ``project``. Keep it as an identity, not a fabricated URL.
                "project_id": row.get("project_id") or row.get("project"),
            }
            try:
                records.append(make_sample(
                    dataset=self.dataset_name, release=release, original_split=record_split,
                    source=source, label=label, original_row_index=index,
                    original_id=None if original_id is None else str(original_id), **metadata,
                ))
            except SchemaError as exc:
                quarantine.append({"row_index": index, "reason": str(exc), "original_id": original_id})
        return records, quarantine


def _list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if x is not None]
    return [str(value)]


class PrimeVulAdapter(JsonlFunctionAdapter):
    def __init__(self):
        super().__init__("primevul")


class DiverseVulAdapter(JsonlFunctionAdapter):
    def __init__(self):
        super().__init__("diversevul")
