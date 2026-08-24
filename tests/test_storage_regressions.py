import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from backend.core.storage import JsonStore, StorageCorruptionError
from backend.core.repository import ChatRepository, WorldRepository


def test_storage_rejects_path_escape(tmp_path):
    store = JsonStore(str(tmp_path / "data"))
    with pytest.raises(ValueError):
        store.path("..", "outside.json")


def test_storage_reports_corrupt_json(tmp_path):
    store = JsonStore(str(tmp_path / "data"))
    path = store.path("broken.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(StorageCorruptionError):
        store.read("broken.json")


def test_storage_roundtrip(tmp_path):
    store = JsonStore(str(tmp_path / "data"))
    value = {"nome": "teste", "valor": [1, 2, 3]}
    store.write(value, "a", "b.json")
    assert store.read("a", "b.json") == value


def test_chat_append_is_serializable(tmp_path):
    store = JsonStore(str(tmp_path / "data"))
    worlds = WorldRepository(store)
    chats = ChatRepository(store, worlds)
    worlds.ensure("001")
    chats.create("001", "001")
    chats.append("001", "001", "user", "olá")
    data = chats.get("001", "001")
    assert len(data["mensagens"]) == 1
    json.dumps(data, ensure_ascii=False)


def test_chat_append_concurrent_does_not_crash(tmp_path):
    store = JsonStore(str(tmp_path / "data"))
    worlds = WorldRepository(store)
    chats = ChatRepository(store, worlds)
    worlds.ensure("001")
    chats.create("001", "001")

    def append(i):
        chats.append("001", "001", "user", f"msg-{i}")

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(append, range(24)))

    data = chats.get("001", "001")
    assert len(data["mensagens"]) == 24
