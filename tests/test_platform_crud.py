import importlib
import sys


def load_app(monkeypatch, tmp_path):
    monkeypatch.setenv("RPG_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("RPG_LLM_URL", "http://127.0.0.1:9")
    sys.modules.pop("backend.app", None)
    return importlib.import_module("backend.app")


def test_memory_crud(monkeypatch, tmp_path):
    mod = load_app(monkeypatch, tmp_path)
    client = mod.app.test_client()
    world = client.post("/api/worlds", json={"nome": "CRUD"}).get_json()["mundo"]
    wid = world["id"]
    created = client.post(f"/api/v2/worlds/{wid}/memory", json={"conteudo": "Fato importante", "importancia": 0.8}).get_json()["memoria"]
    mid = created["id"]
    updated = client.patch(f"/api/v2/worlds/{wid}/memory/{mid}", json={"tipo": "evento", "tags": ["teste"]})
    assert updated.status_code == 200
    assert updated.get_json()["memoria"]["tipo"] == "evento"
    assert client.delete(f"/api/v2/worlds/{wid}/memory/{mid}").status_code == 200
    assert client.get(f"/api/v2/worlds/{wid}/memory/{mid}").status_code == 404


def test_notebook_source_lifecycle(monkeypatch, tmp_path):
    mod = load_app(monkeypatch, tmp_path)
    client = mod.app.test_client()
    wid = client.post("/api/worlds", json={"nome": "Notebook"}).get_json()["mundo"]["id"]
    created = client.post(f"/api/v2/worlds/{wid}/rag/source", json={"title": "Regra", "text": "A cidade possui uma mina de ferro."})
    assert created.status_code == 201
    sid = created.get_json()["source"]["source_id"]
    search = client.get(f"/api/v2/worlds/{wid}/rag/search?q=mina")
    assert search.status_code == 200
    assert search.get_json()["resultados"]
    assert client.post(f"/api/v2/worlds/{wid}/rag/sources/{sid}/reindex").status_code == 200
    assert client.delete(f"/api/v2/worlds/{wid}/rag/sources/{sid}").status_code == 200
    assert client.get(f"/api/v2/worlds/{wid}/rag/sources").get_json()["fontes"] == []
