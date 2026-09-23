from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Scope:
    id: int
    parent: "Scope | None" = None
    bindings: dict[str, str] = field(default_factory=dict)

    def declare(self, name: str, occurrence_id: int) -> str:
        binding = f"{self.id}:{occurrence_id}:{name}"
        self.bindings[name] = binding
        return binding

    def resolve(self, name: str) -> str | None:
        scope: Scope | None = self
        while scope is not None:
            if name in scope.bindings:
                return scope.bindings[name]
            scope = scope.parent
        return None


class ScopeResolver:
    def __init__(self):
        self._next = 0

    def new_scope(self, parent: Scope | None = None) -> Scope:
        scope = Scope(self._next, parent)
        self._next += 1
        return scope

