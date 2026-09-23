from __future__ import annotations

import dataclasses
import re
from typing import Any

from .byte_spans import character_offsets_to_bytes
from astguard.utils.hashing import object_hash


@dataclasses.dataclass(frozen=True)
class EncodedSource:
    input_ids: list[int]
    attention_mask: list[bool]
    special_tokens_mask: list[bool]
    offsets_char: list[tuple[int, int]]
    offsets_byte: list[tuple[int, int]]
    original_bpe_length: int
    retained_bpe_length: int
    all_source_offsets_byte: list[tuple[int,int]] = dataclasses.field(default_factory=list)


class CanonicalTokenizer:
    def __init__(self, checkpoint: str = "microsoft/codebert-base", revision: str | None = None, tokenizer: Any = None):
        if tokenizer is None:
            try:
                from transformers import AutoTokenizer  # type: ignore
            except ImportError as exc:
                raise RuntimeError("CanonicalTokenizer requires the 'research' dependencies") from exc
            tokenizer = AutoTokenizer.from_pretrained(checkpoint, revision=revision, use_fast=True)
        if not getattr(tokenizer, "is_fast", False):
            raise ValueError("a fast tokenizer with source offsets is required")
        self.tokenizer = tokenizer
        self.identity_hash=object_hash({"backend":tokenizer.backend_tokenizer.to_str(),
            "special_ids":tokenizer.all_special_ids})

    def encode(self, source: str, max_length: int = 512) -> EncodedSource:
        full = self.tokenizer(source, add_special_tokens=False, return_offsets_mapping=True, truncation=False)
        original_length = len(full["input_ids"])
        retained_ids = list(full["input_ids"][: max_length - 2])
        retained_offsets = [tuple(x) for x in full["offset_mapping"][: max_length - 2]]
        input_ids = self.tokenizer.build_inputs_with_special_tokens(retained_ids)
        # CodeBERT/RoBERTa adds exactly one special at either end.
        if len(input_ids) != len(retained_ids) + 2:
            raise ValueError("controlled tokenizer must add exactly two special tokens")
        offsets_char = [(0, 0), *retained_offsets, (0, 0)]
        special = [True, *([False] * len(retained_ids)), True]
        return EncodedSource(
            input_ids=input_ids, attention_mask=[True] * len(input_ids), special_tokens_mask=special,
            offsets_char=offsets_char, offsets_byte=character_offsets_to_bytes(source, offsets_char),
            original_bpe_length=original_length, retained_bpe_length=len(retained_ids),
            all_source_offsets_byte=character_offsets_to_bytes(source,[tuple(x) for x in full['offset_mapping']]),
        )


class SmokeTokenizer:
    """Deterministic tokenizer for plumbing tests only; never a scientific model input."""

    _piece = re.compile(r"\w+|[^\w\s]", re.UNICODE)
    identity_hash = "smoke-tokenizer-v1"

    def encode(self, source: str, max_length: int = 512) -> EncodedSource:
        matches = list(self._piece.finditer(source))
        kept = matches[: max_length - 2]
        offsets = [(0, 0), *((m.start(), m.end()) for m in kept), (0, 0)]
        ids = [0] + [2 + (sum(m.group().encode("utf-8")) % 4093) for m in kept] + [1]
        return EncodedSource(
            ids, [True] * len(ids), [True] + [False] * len(kept) + [True], offsets,
            character_offsets_to_bytes(source, offsets), len(matches), len(kept),
            character_offsets_to_bytes(source,[(m.start(),m.end()) for m in matches]),
        )
