"""Extraction-only masking of annotation macros (protocol revision R1).

The word list was fixed from documented Linux sparse/section annotations and
Windows SDK calling-convention macros before measuring coverage; it must not
be extended from observed parse failures. Only lexer identifier tokens are
masked, never string or comment contents. Every masked name is ASCII and is
replaced by the same number of spaces, so byte offsets are preserved. The
tokenizer never sees the masked text, and masked tokens receive no edges.
"""
from __future__ import annotations

from astguard.parsing.lexical import LexToken

ANNOTATION_MACROS_V1 = {
    "linux_sparse": ("__user", "__kernel", "__iomem", "__force", "__rcu", "__percpu", "__bitwise", "__safe",
                     "__nocast", "__private"),
    "linux_attribute": ("__init", "__exit", "__initdata", "__always_inline", "noinline", "asmlinkage", "__cold",
                        "__hot", "__pure", "__must_check", "__maybe_unused", "__used", "notrace", "__weak",
                        "__sched", "__visible"),
    "windows_calling_convention": ("WINAPI", "CALLBACK", "APIENTRY", "STDMETHODCALLTYPE", "STDAPICALLTYPE"),
}
ANNOTATION_MASKING_MODES = ("a_priori_v1", "none")
_WORDS_V1 = frozenset(word for words in ANNOTATION_MACROS_V1.values() for word in words)


def mask_annotation_macros(source: str, tokens: list[LexToken], mode: str = "a_priori_v1") -> tuple[str, list[int]]:
    """Return the extraction source and the ids of masked lexical tokens."""
    if mode not in ANNOTATION_MASKING_MODES:
        raise ValueError(f"unsupported annotation masking mode: {mode}")
    if mode == "none":
        return source, []
    masked = [t for t in tokens if t.kind == "identifier" and t.text in _WORDS_V1]
    if not masked:
        return source, []
    chars = list(source)
    for token in masked:
        chars[token.start_char:token.end_char] = " " * (token.end_char - token.start_char)
    return "".join(chars), [t.id for t in masked]
