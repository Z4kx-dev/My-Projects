from __future__ import annotations

import json
from .store import MemoryStore
from backend.core.repository import ChatRepository, WorldRepository


class ContextBuilder:
    def __init__(self, worlds: WorldRepository, chats: ChatRepository, memories: MemoryStore, max_chars: int = 120000):
        self.worlds, self.chats, self.memories = worlds, chats, memories
        self.max_chars = max_chars

    def build(self, world_id: str, chat_id: str, query: str) -> str:
        world = self.worlds.get(world_id) or {}
        chat = self.chats.get(world_id, chat_id) or {}
        memories = self.memories.search(world_id, query, 16)
        messages = chat.get("mensagens", [])
        recent = messages[-31:-1] if messages else []
        sections = ["[ESTADO DO MUNDO]\n" + json.dumps(world, ensure_ascii=False)]
        if memories:
            sections.append("[MEMÓRIAS RELEVANTES]\n" + "\n".join(json.dumps(m, ensure_ascii=False) for m in memories))
        if recent:
            sections.append("[CONVERSA RECENTE]\n" + "\n".join(f"{m.get('role')}: {m.get('content')}" for m in recent))
        return "\n\n".join(sections)[: self.max_chars]
