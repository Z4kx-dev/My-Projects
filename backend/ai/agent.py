from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .client import OllamaClient, LLMError
from .orchestrator import RPGOrchestrator
from backend.platform.ai_guard import AIGuard
from backend.tools.registry import ToolRegistry


@dataclass
class AgentResult:
    answer: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0


class RPGAgent:
    """Loop de agente determinístico: contexto -> LLM -> tools -> contexto atualizado."""

    def __init__(self, llm: OllamaClient, orchestrator: RPGOrchestrator, tools: ToolRegistry, guard: AIGuard | None = None, max_iterations: int = 6):
        self.llm = llm
        self.orchestrator = orchestrator
        self.tools = tools
        self.guard = guard
        self.max_iterations = max(1, max_iterations)

    def run(self, world_id: str, chat_id: str, user_text: str, options: dict[str, Any] | None = None) -> AgentResult:
        messages = self.orchestrator.messages(world_id, chat_id, user_text)
        calls: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []
        for iteration in range(1, self.max_iterations + 1):
            raw = self.llm.chat(messages, stream=False, options=options, tools=self.tools.definitions())
            if not isinstance(raw, dict):
                return AgentResult(str(raw), calls, results, iteration)
            message = raw.get("message") or {}
            tool_calls = message.get("tool_calls") or []
            content = str(message.get("content") or "")
            messages.append(message)
            if not tool_calls:
                return AgentResult(content, calls, results, iteration)
            for call in tool_calls:
                function = call.get("function") or {}
                name = str(function.get("name") or "")
                arguments = function.get("arguments") or {}
                if not name:
                    continue
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError as exc:
                        result = {"ok": False, "erro": f"Argumentos JSON inválidos: {exc}"}
                        results.append({"tool": name, "result": result})
                        messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})
                        continue
                if not isinstance(arguments, dict):
                    arguments = {}
                try:
                    if self.guard is not None:
                        self.guard.check(name, arguments)
                    value = self.tools.call(name, arguments)
                    result = {"ok": True, "resultado": value}
                except Exception as exc:
                    result = {"ok": False, "erro": str(exc)}
                calls.append({"tool": name, "arguments": arguments})
                results.append({"tool": name, "result": result})
                messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False, default=str)})
        return AgentResult("O agente atingiu o limite de iterações sem concluir a ação.", calls, results, self.max_iterations)
