from __future__ import annotations

from typing import Any
from .storage import JsonStore
from .models import WorldState, Message, utc_now


class WorldRepository:
    def __init__(self, store: JsonStore):
        self.store = store

    def get(self, world_id: str) -> dict[str, Any] | None:
        return self.store.read("mundos", world_id, "mundo.json")

    def save(self, world: dict[str, Any]) -> None:
        world["atualizado_em"] = utc_now()
        self.store.write(world, "mundos", str(world["id"]), "mundo.json")

    def ensure(self, world_id: str, nome: str | None = None, tipo: str = "real") -> dict[str, Any]:
        current = self.get(world_id)
        if current:
            return current
        world = WorldState(id=world_id, nome=nome or f"Mundo {world_id}", tipo=tipo).to_dict()
        self.save(world)
        return world

    def list(self) -> list[dict[str, Any]]:
        root = self.store.path("mundos")
        if not root.exists():
            return []
        result = []
        for directory in sorted(root.iterdir()):
            if directory.is_dir():
                world = self.get(directory.name)
                if world:
                    result.append(world)
        return result


class ChatRepository:
    def __init__(self, store: JsonStore, worlds: WorldRepository):
        self.store, self.worlds = store, worlds

    def new_parts(self, world_id: str, chat_id: str) -> tuple[str, ...]:
        return ("mundos", world_id, "chats", f"{chat_id}.json")

    def legacy_parts(self, world_id: str, chat_id: str) -> tuple[str, ...]:
        return ("mundos", world_id, "chat", f"{chat_id}.json")

    def get(self, world_id: str, chat_id: str) -> dict[str, Any] | None:
        current = self.store.read(*self.new_parts(world_id, chat_id))
        if current is not None:
            return current
        return self.store.read(*self.legacy_parts(world_id, chat_id))

    def save(self, chat: dict[str, Any]) -> None:
        chat["atualizado_em"] = utc_now()
        self.store.write(chat, *self.new_parts(chat["world_id"], chat["id"]))

    def create(self, world_id: str, chat_id: str, nome: str = "Nova conversa") -> dict[str, Any]:
        chat = {"id": chat_id, "world_id": world_id, "nome": nome, "criado_em": utc_now(), "atualizado_em": utc_now(), "mensagens": []}
        self.save(chat)
        return chat

    def append(self, world_id: str, chat_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        chat = self.get(world_id, chat_id)
        if not chat:
            raise FileNotFoundError("Chat não encontrado")
        chat.setdefault("mensagens", []).append(Message(role=role, content=content, metadata=metadata or {}).__dict__)
        self.save(chat)
        return chat

    def list(self, world_id: str) -> list[dict[str, Any]]:
        roots = [self.store.path("mundos", world_id, "chats"), self.store.path("mundos", world_id, "chat")]
        result: dict[str, dict[str, Any]] = {}
        for root in roots:
            if not root.exists():
                continue
            for p in root.glob("*.json"):
                chat = self.store.read(*(("mundos", world_id, root.name, p.name)))
                if chat:
                    result[str(chat["id"])] = {"id": chat["id"], "nome": chat.get("nome", "Chat"), "criado_em": chat.get("criado_em"), "atualizado_em": chat.get("atualizado_em"), "mensagens": len(chat.get("mensagens", []))}
        return [result[k] for k in sorted(result)]
