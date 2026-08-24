from unittest.mock import Mock, patch

from backend.ai.client import OllamaClient


def test_streaming_stops_when_cancelled():
    response = Mock()
    response.raise_for_status.return_value = None
    response.iter_lines.return_value = [
        '{"message":{"content":"um"}}',
        '{"message":{"content":"dois"}}',
    ]
    cancelled = False

    def cancel():
        return cancelled

    with patch("backend.ai.client.requests.post", return_value=response):
        stream = OllamaClient(url="http://llm", model="test").chat([], stream=True, cancel=cancel)
        assert list(stream) == ["um", "dois"]
        response.close.assert_called_once()
