from __future__ import annotations

import dataclasses
from collections import deque

from .cfg import StructuredCFG


@dataclasses.dataclass(frozen=True)
class Definition:
    binding_id: str
    occurrence_id: int


@dataclasses.dataclass
class ReachingResult:
    incoming: dict[int, frozenset[Definition]]
    outgoing: dict[int, frozenset[Definition]]
    dependency_edges: list[tuple[int, int]]


class ReachingDefinitions:
    def solve(self, cfg: StructuredCFG, entry_definitions: set[Definition] | None = None, max_updates: int = 1_000_000) -> ReachingResult:
        entry_definitions = entry_definitions or set()
        incoming = {node: frozenset() for node in cfg.events}
        outgoing = {node: frozenset() for node in cfg.events}
        predecessors = cfg.predecessors
        reachable, pending = set(), [cfg.entry]
        while pending:
            current = pending.pop()
            if current not in reachable:
                reachable.add(current)
                pending.extend(cfg.successors.get(current, ()))
        queue = deque(sorted(reachable))
        updates = 0
        while queue:
            node_id = queue.popleft()
            updates += 1
            if updates > max_updates:
                raise TimeoutError("reaching-definitions resource limit exceeded")
            pred_defs = set(entry_definitions if node_id == cfg.entry else ())
            for predecessor in predecessors[node_id]:
                pred_defs.update(outgoing[predecessor])
            event = cfg.events[node_id]
            out_defs = set(pred_defs)
            if event.kind == "write" and event.binding_id and event.occurrence_id is not None:
                out_defs = {d for d in out_defs if d.binding_id != event.binding_id}
                out_defs.add(Definition(event.binding_id, event.occurrence_id))
            new_in, new_out = frozenset(pred_defs), frozenset(out_defs)
            if new_in != incoming[node_id] or new_out != outgoing[node_id]:
                incoming[node_id], outgoing[node_id] = new_in, new_out
                queue.extend(sorted(cfg.successors.get(node_id, ())))
        edges: set[tuple[int, int]] = set()
        for node_id, event in cfg.events.items():
            if node_id not in reachable:
                continue
            if event.kind == "read" and event.binding_id and event.occurrence_id is not None:
                for definition in incoming[node_id]:
                    if definition.binding_id == event.binding_id:
                        edges.add((event.occurrence_id, definition.occurrence_id))
            if event.kind == "write" and event.occurrence_id is not None:
                edges.update((event.occurrence_id, read) for read in event.rhs_reads if read != event.occurrence_id)
        return ReachingResult(incoming, outgoing, sorted(edges))
