from __future__ import annotations

import dataclasses
import re
from typing import Iterator

from astguard.utils.hashing import sha256_text


_TOKEN = re.compile(
    r"(?P<ws>\s+)|(?P<line>//[^\n]*)|(?P<block>/\*.*?\*/)|"
    r'(?P<rawstring>(?:u8|u|U|L)?R"(?P<delimiter>[^ ()\\\t\r\n]{0,16})\(.*?\)(?P=delimiter)")|'
    r"(?P<string>(?:u8|u|U|L)?(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'))|"
    r"(?P<number>0[xX][0-9A-Fa-f']+|0[bB][01']+|(?:\d[\d']*)(?:\.\d[\d']*)?(?:[eEpP][+-]?\d+)?[uUlLfF]*)|"
    r"(?P<identifier>[A-Za-z_]\w*)|"
    r"(?P<operator>::|->\*|->|\.\*|<<=|>>=|\+\+|--|&&|\|\||==|!=|<=|>=|"
    r"\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>|##|\.\.\.|[{}()\[\];,.?:~!+\-*/%&|^<>=#])|"
    r"(?P<unknown>.)",
    re.DOTALL,
)


@dataclasses.dataclass(frozen=True)
class LexToken:
    id: int
    kind: str
    text: str
    start_char: int
    end_char: int
    start_byte: int
    end_byte: int
    binding_id: str | None = None


def char_to_byte_map(source: str) -> list[int]:
    result = [0]
    offset = 0
    for char in source:
        offset += len(char.encode("utf-8"))
        result.append(offset)
    return result


def lex(source: str, include_comments: bool = False) -> list[LexToken]:
    byte_map = char_to_byte_map(source)
    tokens: list[LexToken] = []
    cursor = 0
    for match in _TOKEN.finditer(source):
        if match.start() != cursor:
            raise ValueError(f"lexer gap at character {cursor}")
        cursor = match.end()
        kind = match.lastgroup or "unknown"
        if kind == 'rawstring':
            kind = 'string'
        if kind == 'unknown':
            raise ValueError(f'unsupported lexical character at {match.start()}')
        if source.startswith('/*',match.start()) and kind != 'block':
            raise ValueError('unterminated block comment')
        if kind == "ws" or (kind in {"line", "block"} and not include_comments):
            continue
        tokens.append(LexToken(
            id=len(tokens), kind=kind, text=match.group(), start_char=match.start(),
            end_char=match.end(), start_byte=byte_map[match.start()], end_byte=byte_map[match.end()],
        ))
    if cursor != len(source):
        raise ValueError(f"lexer stopped at character {cursor}")
    return tokens


def lexical_fingerprint(source: str) -> tuple[str, list[str]]:
    tokens = lex(source)
    values = [f"{token.kind}:{token.text}" for token in tokens]
    return sha256_text("\x1f".join(values)), values


def shingle_set(tokens: list[str], width: int = 5) -> frozenset[str]:
    if len(tokens) < width:
        return frozenset()
    return frozenset(sha256_text("\x1e".join(tokens[i:i + width])) for i in range(len(tokens) - width + 1))
