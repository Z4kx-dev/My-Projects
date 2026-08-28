from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

from .client import OllamaClient
from .orchestrator import RPGOrchestrator
from backend.platform.ai_guard import Decision, ToolPolicy
from backend.tools.registry import ToolRegistry


@dataclass
class AgentResult:
    answer: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0


class RPGAgent:
    """Agente com ciclo controlado e sem enviar definições de tools em perguntas comuns."""

    def __init__(self, llm: OllamaClient, orchestrator: RPGOrchestrator, tools: ToolRegistry, max_iterations: int = 6):
        self.llm = llm
        self.orchestrator = orchestrator
        self.tools = tools
        self.policy = ToolPolicy()
        self.max_iterations = max(1, max_iterations)

    @staticmethod
    def _needs_tools(text: str) -> bool:
        """Heurística barata: perguntas conversacionais não precisam carregar o schema das tools."""
        t = text.casefold()
        web_terms = ("pesquise", "pesquisa", "busque", "buscar", "procure", "na internet", "na web", "notícia", "noticias", "preço", "precos", "cotação", "cotacao", "hoje", "atualmente", "agora")
        action_terms = ("crie", "criar", "delete", "apague", "remova", "altere", "mude", "salve", "atualize", "execute", "construa", "compre", "venda", "ataque", "ande", "viaje", "treine", "use a ferramenta")
        return any(term in t for term in web_terms + action_terms)

    def _tool_round(self, messages: list[dict[str, Any]], calls: list, results: list, options: dict[str, Any] | None, cancel: Callable[[], bool] | None, use_tools: bool) -> tuple[str, bool, dict[str, Any]]:
        if cancel and cancel():
            raise RuntimeError("Execução cancelada pelo usuário.")
        raw = self.llm.chat(
            messages,
            stream=False,
            options=options,
            tools=self.tools.definitions() if use_tools else None,
            cancel=cancel,
        )
        if not isinstance(raw, dict):
            return str(raw), False, {}
        message = raw.get("message") or {}
        tool_calls = message.get("tool_calls") or [] if use_tools else []
        content = str(message.get("content") or "")
        messages.append(message)
        for call in tool_calls:
            if cancel and cancel():
                raise RuntimeError("Execução cancelada pelo usuário.")
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
            arguments = dict(arguments) if isinstance(arguments, dict) else {}
            try:
                reason = str(arguments.pop("reason", "ação solicitada pelo estado atual do mundo"))
                self.policy.check(Decision(name, arguments, reason))
                value = self.tools.call(name, arguments)
                result = {"ok": True, "resultado": value}
            except Exception as exc:
                result = {"ok": False, "erro": str(exc)}
            calls.append({"tool": name, "arguments": dict(arguments)})
            results.append({"tool": name, "result": result})
            messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False, default=str)})
        return content, bool(tool_calls), message

    def run(self, world_id: str, chat_id: str, user_text: str, options: dict[str, Any] | None = None, cancel: Callable[[], bool] | None = None) -> AgentResult:
        messages = self.orchestrator.messages(world_id, chat_id, user_text)
        calls: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []
        use_tools = self._needs_tools(user_text)
        for iteration in range(1, self.max_iterations + 1):
            content, has_tools, _ = self._tool_round(messages, calls, results, options, cancel, use_tools)
            if not has_tools:
                return AgentResult(content, calls, results, iteration)
            use_tools = True
        return AgentResult("O agente atingiu o limite de iterações sem concluir a ação.", calls, results, self.max_iterations)

    def stream(self, world_id: str, chat_id: str, user_text: str, options: dict[str, Any] | None = None, cancel: Callable[[], bool] | None = None) -> Iterator[str]:
        messages = self.orchestrator.messages(world_id, chat_id, user_text)
        calls: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []
        use_tools = self._needs_tools(user_text)
        for iteration in range(1, self.max_iterations + 1):
            content, has_tools, _ = self._tool_round(messages, calls, results, options, cancel, use_tools)
            if not has_tools:
                if content:
                    yield content
                return
            use_tools = True
        yield "O agente atingiu o limite de iterações sem concluir a ação."
