from __future__ import annotations

import json
import logging
from typing import Any, Callable
from .store import MemoryStore
from backend.core.repository import ChatRepository, WorldRepository

log = logging.getLogger(__name__)


class ContextBuilder:
    def __init__(self, worlds: WorldRepository, chats: ChatRepository, memories: MemoryStore, max_chars: int = 120000):
        self.worlds, self.chats, self.memories = worlds, chats, memories
        self.max_chars = max_chars
        self.rag_provider: Callable[[str, str], tuple[str, list[Any]]] | None = None

    @staticmethod
    def _compact_world(world: dict[str, Any]) -> dict[str, Any]:
        """Preserva metadados e estado útil sem despejar estruturas administrativas enormes no prompt."""
        if not isinstance(world, dict):
            return {}
        result: dict[str, Any] = {}
        preferred = ("id", "nome", "tipo", "descricao", "regras", "tempo", "calendario", "estado", "jogador", "entidades", "recursos", "economia", "politica", "clima")
        for key in preferred:
            if key in world:
                result[key] = world[key]
        if not result:
            result = dict(world)
        return result

    def build(self, world_id: str, chat_id: str, query: str) -> str:
        world = self.worlds.get(world_id) or {}
        chat = self.chats.get(world_id, chat_id) or {}
        memories = self.memories.search(world_id, query, 16)
        messages = chat.get("mensagens", [])
        recent = messages[-31:-1] if messages else []
        sections = ["[ESTADO DO MUNDO]\n" + json.dumps(self._compact_world(world), ensure_ascii=False, default=str)]
        if memories:
            sections.append("[MEMÓRIAS RELEVANTES]\n" + "\n".join(json.dumps(m, ensure_ascii=False, default=str) for m in memories))
        if self.rag_provider is not None:
            try:
                rag_text, refs = self.rag_provider(world_id, query)
                if rag_text:
                    sections.append("[FONTES DO NOTEBOOK]\n" + rag_text)
                if refs:
                    sections.append("[CITAÇÕES]\n" + "\n".join(json.dumps(getattr(r, "__dict__", r), ensure_ascii=False, default=str) for r in refs))
            except Exception:
                log.exception("Falha no RAG para world_id=%s", world_id)
        if recent:
            sections.append("[CONVERSA RECENTE]\n" + "\n".join(f"{m.get('role')}: {m.get('content')}" for m in recent))
        return "\n\n".join(sections)[: self.max_chars]
