from unittest.mock import Mock, patch

import pytest

from backend.web.client import WebClient, WebError


def client(monkeypatch, provider="tavily"):
    monkeypatch.setenv("RPG_WEB_PROVIDER", provider)
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    return WebClient()


def test_web_requires_provider_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    client = WebClient()
    assert client.status()["enabled"] is False
    with pytest.raises(WebError):
        client.search("teste")


def test_tavily_search_is_normalized(monkeypatch):
    web = client(monkeypatch)
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"results": [{"title": "Exemplo", "url": "https://example.com", "content": "conteúdo", "score": 0.8, "published_date": "2026-08-25"}]}
    with patch.object(web.session, "post", return_value=response):
        result = web.search("exemplo", 4, topic="news", time_range="week")
    assert result[0]["title"] == "Exemplo"
    assert result[0]["url"] == "https://example.com"
    assert result[0]["score"] == 0.8
    payload = web.session.post.call_args.kwargs["json"]
    assert payload["topic"] == "news"
    assert payload["time_range"] == "week"


def test_open_rejects_non_http(monkeypatch):
    web = client(monkeypatch)
    with pytest.raises(WebError):
        web.open("file:///etc/passwd")


def test_open_blocks_localhost(monkeypatch):
    web = client(monkeypatch)
    with pytest.raises(WebError, match="localhost"):
        web.open("http://localhost:5000/api/health")


def test_open_blocks_private_ip(monkeypatch):
    web = client(monkeypatch)
    with pytest.raises(WebError):
        web.open("http://127.0.0.1:5000/")


def test_search_rejects_invalid_topic(monkeypatch):
    web = client(monkeypatch)
    with pytest.raises(WebError):
        web.search("teste", topic="invalid")


def test_direct_open_rejects_non_text(monkeypatch):
    web = client(monkeypatch)
    response = Mock()
    response.raise_for_status.return_value = None
    response.url = "https://example.com/file"
    response.headers = {"Content-Type": "application/pdf"}
    response.close.return_value = None
    with patch.object(web.session, "get", return_value=response), patch.object(web, "_validate_public_url"):
        with pytest.raises(WebError, match="conteúdo textual"):
            web._direct_open("https://example.com/file")


def test_direct_open_strips_html(monkeypatch):
    web = client(monkeypatch)
    response = Mock()
    response.raise_for_status.return_value = None
    response.url = "https://example.com/page"
    response.headers = {"Content-Type": "text/html; charset=utf-8"}
    response.encoding = "utf-8"
    response.iter_content.return_value = [b"<html><script>x</script><body><h1>Titulo</h1> Texto</body></html>"]
    response.close.return_value = None
    with patch.object(web.session, "get", return_value=response), patch.object(web, "_validate_public_url"):
        result = web._direct_open("https://example.com/page")
    assert "Titulo" in result["content"]
    assert "Texto" in result["content"]
    assert "script" not in result["content"].lower()
