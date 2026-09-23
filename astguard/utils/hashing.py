from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def object_hash(value: Any) -> str:
    return sha256_text(canonical_json(value))


def ordered_ids_hash(values: Iterable[str]) -> str:
    return sha256_text("\n".join(values))


def hash_uniform(namespace: str, value: str) -> float:
    raw = hashlib.sha256(f"{namespace}|{value}".encode()).digest()[:8]
    return int.from_bytes(raw, "big") / 2**64

