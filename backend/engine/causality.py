from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Cause:
    event_id: str
    parents: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)


class CausalityGraph:
    def __init__(self):
        self.nodes: dict[str, Cause] = {}

    def add(self, event_id: str, parents: list[str] | None = None, effects: list[str] | None = None, facts: dict[str, Any] | None = None) -> Cause:
        node = Cause(event_id, parents or [], effects or [], facts or {})
        self.nodes[event_id] = node
        return node

    def explain(self, event_id: str, depth: int = 8) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        stack = [(event_id, 0)]
        while stack:
            current, level = stack.pop()
            if current in seen or level > depth:
                continue
            seen.add(current)
            result.append(current)
            node = self.nodes.get(current)
            if node:
                stack.extend((parent, level + 1) for parent in node.parents)
        return result
