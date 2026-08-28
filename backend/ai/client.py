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
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        # 55s era curto demais para o primeiro carregamento do modelo no Codespaces.
        # O Ollama pode gastar vários segundos carregando o GGUF antes de gerar tokens.
        self.timeout = max(10.0, float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120")))
        self.num_predict = max(32, int(os.getenv("OLLAMA_NUM_PREDICT", "128")))
        self.keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "10m")

    def chat(
        self,
        messages: list[dict[str, Any]],
        stream: bool = False,
        options: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        cancel: Callable[[], bool] | None = None,
    ) -> Iterator[str] | str | dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "keep_alive": self.keep_alive,
        }
        effective_options = dict(options or {})
        effective_options.setdefault("num_predict", self.num_predict)
        if effective_options:
            payload["options"] = effective_options
        if tools:
            payload["tools"] = tools
        try:
            response = requests.post(
                f"{self.url}/api/chat",
                json=payload,
                stream=stream,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMError(f"Falha no provedor LLM: {exc}") from exc
        if not stream:
            try:
                return response.json()
            except ValueError as exc:
                response.close()
                raise LLMError(f"Resposta inválida do provedor LLM: {exc}") from exc

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
