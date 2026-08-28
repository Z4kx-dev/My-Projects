from __future__ import annotations

import json
import os
from collections.abc import Iterator
from typing import Any, Callable
import requests


class LLMError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, url: str | None = None, model: str | None = None):
        self.url = (url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "900"))

    def chat(self, messages: list[dict[str, Any]], stream: bool = False, options: dict[str, Any] | None = None, tools: list[dict[str, Any]] | None = None, cancel: Callable[[], bool] | None = None) -> Iterator[str] | str | dict[str, Any]:
        payload: dict[str, Any] = {"model": self.model, "messages": messages, "stream": stream}
        if options:
            payload["options"] = options
        if tools:
            payload["tools"] = tools
        try:
            response = requests.post(f"{self.url}/api/chat", json=payload, stream=stream, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMError(f"Falha no provedor LLM: {exc}") from exc
        if not stream:
            return response.json()

        def tokens() -> Iterator[str]:
            try:
                for line in response.iter_lines(decode_unicode=True):
                    if cancel and cancel():
                        break
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except ValueError:
                        continue
                    token = (data.get("message") or {}).get("content", "")
                    if token:
                        yield token
            finally:
                response.close()

        return tokens()
