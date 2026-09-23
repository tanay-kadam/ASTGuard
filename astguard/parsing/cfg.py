from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class Event:
    id: int
    kind: str  # read, write, or noop
    binding_id: str | None
    occurrence_id: int | None
    rhs_reads: tuple[int, ...] = ()


@dataclasses.dataclass
class StructuredCFG:
    events: dict[int, Event]
    successors: dict[int, set[int]]
    entry: int

    @property
    def predecessors(self) -> dict[int, set[int]]:
        result = {node: set() for node in self.events}
        for left, targets in self.successors.items():
            for right in targets:
                result[right].add(left)
        return result

    @classmethod
    def linear(cls, events: list[Event]) -> "StructuredCFG":
        if not events:
            events = [Event(0, "noop", None, None)]
        mapping = {event.id: event for event in events}
        successors = {event.id: set() for event in events}
        for left, right in zip(events, events[1:]):
            successors[left.id].add(right.id)
        return cls(mapping, successors, events[0].id)

