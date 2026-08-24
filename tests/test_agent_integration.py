from __future__ import annotations

from backend.ai.agent import RPGAgent
from backend.ai.orchestrator import RPGOrchestrator
from backend.memory.context import ContextBuilder
from backend.tools.registry import ToolRegistry


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, stream=False, options=None, tools=None):
        self.calls += 1
        if self.calls == 1:
            return {"message": {"role": "assistant", "tool_calls": [{"function": {"name": "echo", "arguments": {"value": "ok"}}}]}}
        return {"message": {"role": "assistant", "content": "Ferramenta executada."}}


class FakeWorlds:
    def get(self, _):
        return {"id": "001"}


class FakeChats:
    def get(self, *_):
        return {"mensagens": []}


class FakeMemory:
    def search(self, *_):
        return []


def test_agent_executes_tool_then_answers():
    registry = ToolRegistry()
    registry.register("echo", "teste", {"type": "object", "properties": {"value": {"type": "string"}}}, lambda value: value)
    context = ContextBuilder(FakeWorlds(), FakeChats(), FakeMemory())
    orchestrator = RPGOrchestrator(FakeLLM(), context)
    agent = RPGAgent(orchestrator.llm, orchestrator, registry, max_iterations=3)
    result = agent.run("001", "001", "teste")
    assert result.answer == "Ferramenta executada."
    assert result.tool_calls[0]["tool"] == "echo"
    assert result.tool_results[0]["result"]["ok"] is True
    assert result.iterations == 2
