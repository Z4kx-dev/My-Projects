from unittest.mock import Mock, patch

import pytest

from backend.web.client import WebClient, WebError


def test_web_requires_provider_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    client = WebClient()
    assert client.status()["enabled"] is False
    with pytest.raises(WebError):
        client.search("teste")


def test_tavily_search_is_normalized(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    client = WebClient()
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"results": [{"title": "Exemplo", "url": "https://example.com", "content": "conteúdo", "score": 0.8}]}
    with patch("backend.web.client.requests.Session.post", return_value=response):
        result = client.search("exemplo", 4)
    assert result[0]["title"] == "Exemplo"
    assert result[0]["url"] == "https://example.com"
    assert result[0]["score"] == 0.8


def test_open_rejects_non_http():
    client = WebClient()
    with pytest.raises(WebError):
        client.open("file:///etc/passwd")
