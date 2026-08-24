import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def app_module(monkeypatch, tmp_path):
    monkeypatch.setenv("RPG_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("RPG_LLM_URL", "http://127.0.0.1:9")
    sys.modules.pop("backend.app", None)
    return importlib.import_module("backend.app")


def test_platform_uses_stdlib():
    import platform
    assert hasattr(platform, "system")
    assert platform.system()


def test_health_reports_dependency_failure(app_module):
    response = app_module.app.test_client().get("/api/health")
    assert response.status_code in (200, 503)
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert "ok" in payload
    assert "ollama" in payload


def test_world_and_chat_contracts(app_module):
    client = app_module.app.test_client()
    created = client.post("/api/worlds", json={"nome": "Teste", "tipo": "real"})
    assert created.status_code == 201
    world = created.get_json()["mundo"]
    wid = world["id"]

    chat = client.post(f"/api/worlds/{wid}/chats", json={"nome": "Teste"})
    assert chat.status_code == 201
    cid = chat.get_json()["chat"]["id"]

    assert client.get(f"/api/worlds/{wid}").status_code == 200
    assert client.get(f"/api/worlds/{wid}/chats/{cid}").status_code == 200


def test_invalid_message_is_rejected(app_module):
    client = app_module.app.test_client()
    response = client.post("/api/chat", json={"world_id": "001", "chat_id": "001", "message": ""})
    assert response.status_code == 400
