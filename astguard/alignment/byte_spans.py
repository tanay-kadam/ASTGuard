from __future__ import annotations

from astguard.parsing.lexical import char_to_byte_map


def character_offsets_to_bytes(source: str, offsets: list[tuple[int, int]]) -> list[tuple[int, int]]:
    lookup = char_to_byte_map(source)
    result: list[tuple[int, int]] = []
    for start, end in offsets:
        if start < 0 or end < start or end > len(source):
            raise ValueError(f"invalid character offset {(start, end)}")
        result.append((lookup[start], lookup[end]))
    return result


def overlaps(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] < right[1] and right[0] < left[1]


class ByteSpanAligner:
    def align(
        self,
        token_byte_offsets: list[tuple[int, int]],
        lexical_spans: list[tuple[int, int]],
        special_tokens_mask: list[bool],
        retained_token_count: int | None = None,
    ) -> tuple[dict[int, list[int]], set[int]]:
        if len(token_byte_offsets) != len(special_tokens_mask):
            raise ValueError("offset and special-token arrays differ")
        retained = len(token_byte_offsets) if retained_token_count is None else retained_token_count
        leaf_to_all: dict[int, list[int]] = {}
        leaf_to_retained: dict[int, list[int]] = {}
        for leaf_id, span in enumerate(lexical_spans):
            all_pieces = [i for i, offset in enumerate(token_byte_offsets) if not special_tokens_mask[i] and offset[0] != offset[1] and overlaps(span, offset)]
            kept = [i for i in all_pieces if i < retained]
            leaf_to_all[leaf_id] = all_pieces
            leaf_to_retained[leaf_id] = kept
        eligible = {leaf for leaf, all_pieces in leaf_to_all.items() if all_pieces and leaf_to_retained[leaf] == all_pieces}
        return {leaf: pieces for leaf, pieces in leaf_to_retained.items() if leaf in eligible}, eligible

