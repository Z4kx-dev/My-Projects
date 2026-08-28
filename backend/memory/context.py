from __future__ import annotations

import json
import logging
from typing import Any, Callable
from .store import MemoryStore
from backend.core.repository import ChatRepository, WorldRepository

log = logging.getLogger(__name__)


class ContextBuilder:
    def __init__(self, worlds: WorldRepository, chats: ChatRepository, memories: MemoryStore, max_chars: int = 6000):
        self.worlds, self.chats, self.memories = worlds, chats, memories
        self.max_chars = max(3000, max_chars)
        self.rag_provider: Callable[[str, str], tuple[str, list[Any]]] | None = None

    @staticmethod
    def _compact_world(world: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(world, dict):
            return {}
        # Keep operational state, but avoid dumping large entity/resource arrays into every prompt.
        preferred = ("id", "nome", "tipo", "descricao", "regras", "tempo", "calendario", "estado", "jogador", "economia", "politica", "clima")
        result = {key: world[key] for key in preferred if key in world}
        if "entidades" in world and isinstance(world["entidades"], list):
            result["entidades"] = world["entidades"][-5:]
        if "recursos" in world and isinstance(world["recursos"], dict):
            result["recursos"] = world["recursos"]
        return result or dict(world)

    def build(self, world_id: str, chat_id: str, query: str) -> str:
        world = self.worlds.get(world_id) or {}
        chat = self.chats.get(world_id, chat_id) or {}
        memories = self.memories.search(world_id, query, 3)
        messages = chat.get("mensagens", [])
        recent = messages[-4:-1] if messages else []
        sections = ["[MUNDO]\n" + json.dumps(self._compact_world(world), ensure_ascii=False, default=str)]
        if memories:
            sections.append("[MEMÓRIA]\n" + "\n".join(json.dumps(m, ensure_ascii=False, default=str) for m in memories))
        if self.rag_provider is not None:
            try:
                rag_text, refs = self.rag_provider(world_id, query)
                if rag_text:
                    sections.append("[NOTEBOOK]\n" + rag_text[:2000])
                if refs:
                    sections.append("[FONTES]\n" + "\n".join(json.dumps(getattr(r, "__dict__", r), ensure_ascii=False, default=str) for r in refs[:3]))
            except Exception:
                log.exception("Falha no RAG para world_id=%s", world_id)
        if recent:
            sections.append("[HISTÓRICO]\n" + "\n".join(f"{m.get('role')}: {str(m.get('content', ''))[:600]}" for m in recent))
        return "\n\n".join(sections)[: self.max_chars]
