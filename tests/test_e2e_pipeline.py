from pathlib import Path

from backend.core.storage import JsonStore
from backend.core.repository import ChatRepository, WorldRepository
from backend.memory.store import MemoryStore
from backend.memory.context import ContextBuilder
from backend.rag.notebook import NotebookWorkspace


def test_e2e_world_chat_memory_notebook(tmp_path):
    store = JsonStore(str(tmp_path / "data"))
    worlds = WorldRepository(store)
    chats = ChatRepository(store, worlds)
    memories = MemoryStore(store)
    world = worlds.ensure("001", "E2E")
    chats.create("001", "001")
    chats.append("001", "001", "user", "O reino possui uma mina de ferro.")
    memories.add("001", "A mina de ferro fica ao norte.", "fato", 0.9, ["geografia", "recurso"], "sistema")
    notebook = NotebookWorkspace("001", Path(tmp_path) / "notebooks" / "001")
    notebook.add_text("Regras", "A mina ao norte produz ferro quando há trabalhadores suficientes.")
    context = ContextBuilder(worlds, chats, memories)
    context.rag_provider = lambda wid, query: notebook.context(query, 4)
    built = context.build("001", "001", "mina de ferro")
    assert "ESTADO DO MUNDO" in built
    assert "MEMÓRIAS RELEVANTES" in built
    assert "FONTES DO NOTEBOOK" in built
    assert "mina" in built.lower()
