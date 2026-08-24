import json

from backend.core.storage import JsonStore
from backend.core.repository import WorldRepository, ChatRepository
from backend.memory.store import MemoryStore
from backend.memory.retrieval import HybridRetriever
from backend.engine.simulator import SimulationEngine
from backend.engine.time import WorldClock
from backend.engine.entities import Entity, EntityManager
from backend.engine.economy import EconomyEngine
from backend.engine.society import SocietyEngine
from backend.tools.registry import ToolRegistry


def make(tmp_path):
    store = JsonStore(str(tmp_path))
    worlds = WorldRepository(store)
    chats = ChatRepository(store, worlds)
    memories = MemoryStore(store)
    return store, worlds, chats, memories


def test_storage_atomic_and_json(tmp_path):
    store, *_ = make(tmp_path)
    store.write({"ok": True}, "x", "a.json")
    assert store.read("x", "a.json")["ok"] is True


def test_chat_legacy_read_and_new_write(tmp_path):
    store, worlds, chats, _ = make(tmp_path)
    worlds.ensure("001")
    store.write({"id": "001", "world_id": "001", "mensagens": []}, "mundos", "001", "chat", "001.json")
    assert chats.get("001", "001") is not None
    chats.append("001", "001", "user", "teste")
    assert chats.get("001", "001")["mensagens"][-1]["content"] == "teste"


def test_memory_and_retrieval(tmp_path):
    _, worlds, _, memories = make(tmp_path)
    worlds.ensure("001")
    memories.add("001", "Raphael encontrou uma ponte", importancia=0.9, tags=["ponte"])
    result = HybridRetriever(memories).search("001", "ponte", 5)
    assert result and result[0]["conteudo"].startswith("Raphael")


def test_clock_cannot_reverse():
    clock = WorldClock("2026-01-01T00:00:00+00:00")
    assert clock.advance(60).startswith("2026-01-01T00:01")
    try:
        clock.advance(-1)
        assert False
    except ValueError:
        pass


def test_simulation_event(tmp_path):
    _, worlds, _, _ = make(tmp_path)
    world = worlds.ensure("001")
    engine = SimulationEngine(world)
    engine.advance(3600, "viagem")
    event = engine.event("viagem", "O personagem iniciou uma viagem")
    assert event["tipo"] == "viagem"
    assert len(world["eventos"]) == 1


def test_entity_npc(tmp_path):
    _, worlds, _, _ = make(tmp_path)
    world = worlds.ensure("001")
    manager = EntityManager(world)
    npc = manager.create(Entity("npc-1", "Ana", "npc", objetivos=["sobreviver"]))
    assert npc["nome"] == "Ana"
    action = manager.act_npc("npc-1", [{"descricao": "comer e sobreviver"}, {"descricao": "dormir"}])
    assert "sobreviver" in action["descricao"]


def test_economy_and_society(tmp_path):
    _, worlds, _, _ = make(tmp_path)
    world = worlds.ensure("001")
    economy = EconomyEngine(world)
    economy.stock("madeira", 10)
    economy.stock("madeira", -3)
    economy.price("madeira", 2)
    buyer, seller = {"saldo": 10}, {"saldo": 0}
    trade = economy.transact(buyer, seller, "madeira", 2)
    assert trade["total"] == 4
    society = SocietyEngine(world)
    assert society.create_group("g1", "Guilda")["nome"] == "Guilda"


def test_tool_registry():
    registry = ToolRegistry()
    registry.register("soma", "Soma", {"type": "object"}, lambda a=0, b=0: a + b)
    assert registry.call("soma", {"a": 2, "b": 3}) == 5
    assert registry.definitions()[0]["function"]["name"] == "soma"
