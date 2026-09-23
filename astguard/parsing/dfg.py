from __future__ import annotations

import dataclasses

from .cfg import Event, StructuredCFG
from .lexical import LexToken
from .reaching_defs import Definition, ReachingDefinitions
from .scopes import ScopeResolver


_TYPE_WORDS = {"char","short","int","long","float","double","signed","unsigned","bool","size_t","auto","const","volatile","static","register"}
_UNSUPPORTED = {"goto","switch","case","try","catch","throw","co_await","co_yield"}
_CONTROL = {"if","else","while","do","for","break","continue"}
_ASSIGN = {"=","+=","-=","*=","/=","%=","&=","|=","^=","<<=",">>="}


@dataclasses.dataclass(frozen=True)
class DFGExtraction:
    status: str
    edges: tuple[tuple[int, int], ...]
    binding_by_occurrence: dict[int, str]
    reasons: tuple[str, ...] = ()


class ConservativeDFGExtractor:
    """Sound-for-contract straight-line subset; unsupported control fails closed."""

    def extract(self, tokens: list[LexToken]) -> DFGExtraction:
        words = {token.text for token in tokens}
        unsupported = sorted(words & (_UNSUPPORTED | _CONTROL))
        if unsupported:
            return DFGExtraction("unsupported_control", (), {}, tuple(unsupported))
        resolver = ScopeResolver()
        scope = resolver.new_scope()
        binding_by_occurrence: dict[int, str] = {}
        events: list[Event] = []
        entry: set[Definition] = set()
        event_id = 0

        def emit(kind: str, binding: str | None, occurrence: int | None, rhs=()):
            nonlocal event_id
            events.append(Event(event_id, kind, binding, occurrence, tuple(rhs)))
            event_id += 1

        try:
            open_paren = next(i for i, token in enumerate(tokens) if token.text == "(")
            close_paren = next(i for i in range(open_paren + 1, len(tokens)) if tokens[i].text == ")")
            segment_start = open_paren + 1
            for i in range(open_paren + 1, close_paren + 1):
                if i == close_paren or tokens[i].text == ",":
                    identifiers = [t for t in tokens[segment_start:i] if t.kind == "identifier" and t.text not in _TYPE_WORDS]
                    if identifiers:
                        token = identifiers[-1]
                        binding = scope.declare(token.text, token.id)
                        binding_by_occurrence[token.id] = binding
                        entry.add(Definition(binding, token.id))
                    segment_start = i + 1
        except StopIteration:
            pass

        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token.text == "{":
                scope = resolver.new_scope(scope); index += 1; continue
            if token.text == "}":
                scope = scope.parent or scope; index += 1; continue
            if token.text in _TYPE_WORDS:
                cursor = index
                while cursor < len(tokens) and (tokens[cursor].text in _TYPE_WORDS or tokens[cursor].text in {"*","&"}):
                    cursor += 1
                if cursor < len(tokens) and tokens[cursor].kind == "identifier":
                    if cursor + 1 < len(tokens) and tokens[cursor + 1].text == "(":
                        index = cursor + 1
                        continue
                    declaration = tokens[cursor]
                    binding = scope.declare(declaration.text, declaration.id)
                    binding_by_occurrence[declaration.id] = binding
                    if cursor + 1 < len(tokens) and tokens[cursor + 1].text == "=":
                        end, reads = cursor + 2, []
                        while end < len(tokens) and tokens[end].text != ";":
                            use = tokens[end]
                            resolved = scope.resolve(use.text) if use.kind == "identifier" else None
                            if resolved:
                                binding_by_occurrence[use.id] = resolved; emit("read", resolved, use.id); reads.append(use.id)
                            end += 1
                        emit("write", binding, declaration.id, reads); index = end + 1
                    else:
                        index = cursor + 1
                    continue
            if token.kind == "identifier" and index + 1 < len(tokens) and tokens[index + 1].text in _ASSIGN:
                binding = scope.resolve(token.text)
                if binding is None:
                    return DFGExtraction("unsupported_binding", (), binding_by_occurrence, (token.text,))
                binding_by_occurrence[token.id] = binding
                operator, reads = tokens[index + 1].text, []
                if operator != "=":
                    emit("read", binding, token.id); reads.append(token.id)
                cursor = index + 2
                while cursor < len(tokens) and tokens[cursor].text != ";":
                    use = tokens[cursor]
                    resolved = scope.resolve(use.text) if use.kind == "identifier" else None
                    if resolved:
                        binding_by_occurrence[use.id] = resolved; emit("read", resolved, use.id); reads.append(use.id)
                    cursor += 1
                emit("write", binding, token.id, reads); index = cursor + 1; continue
            if token.kind == "identifier":
                binding = scope.resolve(token.text)
                if binding:
                    binding_by_occurrence[token.id] = binding; emit("read", binding, token.id)
            index += 1
        result = ReachingDefinitions().solve(StructuredCFG.linear(events), entry)
        return DFGExtraction("ok", tuple(result.dependency_edges), binding_by_occurrence)
