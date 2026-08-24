from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
STYLE = (ROOT / "frontend" / "style.css").read_text(encoding="utf-8")


def test_frontend_assets_are_versioned_and_present():
    assert '/static/style.css?v=20260824-2' in INDEX
    assert '/static/app.js?v=20260824-2' in INDEX
    assert (ROOT / "frontend" / "app.js").exists()
    assert (ROOT / "frontend" / "style.css").exists()


def test_loading_overlay_respects_hidden_attribute():
    assert '.loading[hidden]{display:none!important}' in STYLE


def test_composer_has_abort_and_upload_controls():
    assert 'id="stop-button"' in INDEX
    assert 'id="attach-file"' in INDEX
    assert "S.controller?.abort()" in APP
    assert "uploadSource(f)" in APP


def test_frontend_uses_expected_api_contracts():
    for endpoint in ('/api/worlds', '/api/chat', '/api/v2/worlds/${S.worldId}/rag/upload'):
        assert endpoint in APP
