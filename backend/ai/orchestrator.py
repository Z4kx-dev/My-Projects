from __future__ import annotations

from typing import Any
from .client import OllamaClient
from backend.memory.context import ContextBuilder

SYSTEM = """Você é o motor cognitivo de um RPG de simulação persistente. Simule, não escreva roteiro. O estado persistente do mundo é a fonte de verdade. Nunca invente fatos para preencher lacunas. O jogador controla apenas seu personagem. NPCs possuem objetivos, memória, relações e livre-arbítrio. O tempo é irreversível. Recursos são finitos. Consequências persistem. Não revele informações privadas que o personagem não poderia saber. Respeite causalidade, física, biologia, psicologia, sociedade, economia, tecnologia e as regras específicas do mundo."""


class RPGOrchestrator:
    def __init__(self, llm: OllamaClient, context: ContextBuilder):
        self.llm, self.context = llm, context

    def messages(self, world_id: str, chat_id: str, user_text: str) -> list[dict[str, str]]:
        ctx = self.context.build(world_id, chat_id, user_text)
        return [{"role": "system", "content": SYSTEM + "\n\n" + ctx}, {"role": "user", "content": user_text}]

    def run(self, world_id: str, chat_id: str, user_text: str, options: dict[str, Any] | None = None) -> str:
        return str(self.llm.chat(self.messages(world_id, chat_id, user_text), stream=False, options=options))
