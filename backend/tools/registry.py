from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    handler: Callable[..., Any]
    schema: dict[str, Any]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, description: str, schema: dict[str, Any], handler: Callable[..., Any]) -> None:
        if name in self._tools:
            raise ValueError(f"Ferramenta já registrada: {name}")
        self._tools[name] = Tool(name, description, handler, schema)

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Ferramenta desconhecida: {name}") from exc

    def definitions(self) -> list[dict[str, Any]]:
        return [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.schema}} for t in self._tools.values()]

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        return self.get(name).handler(**arguments)
