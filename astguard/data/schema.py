from __future__ import annotations

import dataclasses
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Iterator

from astguard.utils.hashing import sha256_text


class SchemaError(ValueError):
    pass


@dataclasses.dataclass
class SampleRecord:
    sample_id: str
    dataset: str
    release: str
    original_split: str
    source_raw: str
    source_canonical: str
    label: int
    raw_sha256: str
    lexical_sha256: str
    upstream_normalized_hash: str
    original_row_index: int
    component_id: str = ""
    original_id: str | None = None
    project_id: str | None = None
    repository_url: str | None = None
    file_path: str | None = None
    commit_id: str | None = None
    timestamp: str | None = None
    language_metadata: str | None = None
    cwe_ids: list[str] = dataclasses.field(default_factory=list)
    cve_ids: list[str] = dataclasses.field(default_factory=list)
    pair_ids: list[str] = dataclasses.field(default_factory=list)
    view_membership: list[str] = dataclasses.field(default_factory=list)

    def __post_init__(self) -> None:
        if self.label not in (0, 1):
            raise SchemaError(f"label must be binary for {self.sample_id}")
        if self.source_canonical != canonicalize_source(self.source_raw):
            raise SchemaError(f"canonical source mismatch for {self.sample_id}")

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SampleRecord":
        allowed = {f.name for f in dataclasses.fields(cls)}
        extra = set(value) - allowed
        if extra:
            raise SchemaError(f"unknown SampleRecord fields: {sorted(extra)}")
        return cls(**value)


@dataclasses.dataclass
class FeatureRecord:
    sample_id: str
    source_sha256: str
    preprocessing_hash: str
    input_ids: list[int]
    attention_mask: list[bool]
    special_tokens_mask: list[bool]
    offsets_char: list[tuple[int, int]]
    offsets_byte: list[tuple[int, int]]
    original_bpe_length: int
    retained_bpe_length: int
    language_selected: str
    parse_status: str
    ast_status: str
    dfg_status: str
    alignment_status: str
    status_reasons: list[str] = dataclasses.field(default_factory=list)
    unsupported_constructs: list[str] = dataclasses.field(default_factory=list)
    lexical_nodes: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    ast_tree_nodes: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    ast_tree_edges: list[tuple[int, int]] = dataclasses.field(default_factory=list)
    lexical_ast_edges: list[tuple[int, int]] = dataclasses.field(default_factory=list)
    lexical_dfg_edges: list[tuple[int, int]] = dataclasses.field(default_factory=list)
    leaf_to_bpe: dict[int, list[int]] = dataclasses.field(default_factory=dict)
    ast_leaf_to_bpe: dict[int, list[int]] = dataclasses.field(default_factory=dict)
    ast_token_edges: list[tuple[int, int]] = dataclasses.field(default_factory=list)
    dfg_token_edges: list[tuple[int, int]] = dataclasses.field(default_factory=list)
    edge_projection_groups: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    relation_stats: dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self) -> None:
        length = len(self.input_ids)
        arrays = (self.attention_mask, self.special_tokens_mask, self.offsets_char, self.offsets_byte)
        if any(len(x) != length for x in arrays):
            raise SchemaError("feature sequence arrays must have equal length")
        if length > 512:
            raise SchemaError("input length exceeds 512")
        forbidden = {"label", "cwe_ids", "cve_ids", "project_id", "file_path", "pair_ids"}
        if forbidden.intersection(self.relation_stats):
            raise SchemaError("analysis metadata leaked into FeatureRecord")


@dataclasses.dataclass
class SplitManifest:
    view: str
    version: str
    source_hashes: list[str]
    rule_hash: str
    ordered_sample_ids: list[str]
    component_ids: list[str]
    original_splits: list[str]
    roles: list[str]
    exclusion_reasons: dict[str, str]
    link_evidence: list[dict[str, Any]]
    counts: dict[str, int]
    file_hash: str = ""


@dataclasses.dataclass
class PredictionRecord:
    run_id: str
    sample_id: str
    dataset: str
    view: str
    split_hash: str
    model_id: str
    seed: int
    logit: float
    probability: float
    label: int
    threshold_ids: dict[str, str]
    decisions: dict[str, bool]
    checkpoint_hash: str
    feature_hash: str
    metadata_join_reference: str | None = None


def canonicalize_source(source: str) -> str:
    return source.replace("\r\n", "\n")


def make_sample(
    *, dataset: str, release: str, original_split: str, source: str, label: int,
    original_row_index: int, original_id: str | None = None, lexical_sha256: str = "",
    **metadata: Any,
) -> SampleRecord:
    canonical = canonicalize_source(source)
    stable = original_id if original_id is not None else str(original_row_index)
    return SampleRecord(
        sample_id=f"{dataset}:{release}:{stable}", dataset=dataset, release=release,
        original_split=original_split, source_raw=source, source_canonical=canonical,
        label=int(label), raw_sha256=sha256_text(source), lexical_sha256=lexical_sha256,
        upstream_normalized_hash=sha256_text("".join(canonical.split())),
        original_row_index=original_row_index, original_id=original_id, **metadata,
    )


def write_jsonl(path: str | Path, rows: Iterable[Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor,temporary=tempfile.mkstemp(prefix=f".{target.name}.",dir=target.parent)
    try:
        with os.fdopen(descriptor,"w",encoding="utf-8",newline="\n") as handle:
            for row in rows:
                value = row.to_dict() if hasattr(row, "to_dict") else dataclasses.asdict(row) if dataclasses.is_dataclass(row) else row
                handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush();os.fsync(handle.fileno())
        os.replace(temporary,target)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def read_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SchemaError(f"invalid JSONL at line {number}: {exc}") from exc
