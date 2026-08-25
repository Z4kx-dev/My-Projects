from __future__ import annotations

import os
import re
from dataclasses import dataclass, asdict
from typing import Any
from urllib.parse import urlparse

import requests


class WebError(RuntimeError):
    pass


@dataclass
class WebResult:
    title: str
    url: str
    content: str = ""
    score: float | None = None
    source: str = "web"
    published_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WebClient:
    """Cliente web com provedor configurável e limites seguros."""

    def __init__(self) -> None:
        self.provider = os.getenv("RPG_WEB_PROVIDER", "tavily").strip().lower()
        self.tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.brave_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
        self.timeout = max(3, float(os.getenv("RPG_WEB_TIMEOUT_SECONDS", "20")))
        self.max_results = min(20, max(1, int(os.getenv("RPG_WEB_MAX_RESULTS", "8"))))
        self.max_content_chars = min(50000, max(1000, int(os.getenv("RPG_WEB_MAX_CONTENT_CHARS", "12000"))))
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": os.getenv("RPG_WEB_USER_AGENT", "KorczakAI/1.0")})

    @property
    def configured(self) -> bool:
        return bool(self.tavily_key or self.brave_key)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.configured,
            "provider": self.provider,
            "tavily": bool(self.tavily_key),
            "brave": bool(self.brave_key),
        }

    def search(self, query: str, limit: int | None = None, domain: str | None = None) -> list[dict[str, Any]]:
        q = str(query or "").strip()
        if not q:
            raise WebError("A consulta web não pode ser vazia.")
        if len(q) > 400:
            raise WebError("A consulta web excede 400 caracteres.")
        limit = min(self.max_results, max(1, int(limit or self.max_results)))
        if self.provider == "brave" and self.brave_key:
            return self._brave_search(q, limit, domain)
        if self.tavily_key:
            return self._tavily_search(q, limit, domain)
        if self.brave_key:
            return self._brave_search(q, limit, domain)
        raise WebError("Busca web não configurada. Defina TAVILY_API_KEY ou BRAVE_SEARCH_API_KEY.")

    def open(self, url: str, query: str | None = None) -> dict[str, Any]:
        parsed = urlparse(str(url).strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise WebError("URL inválida.")
        if self.tavily_key:
            try:
                return self._tavily_extract(url, query)
            except WebError:
                if self.provider == "tavily" and not self.brave_key:
                    raise
        return self._direct_open(url)

    def _tavily_search(self, query: str, limit: int, domain: str | None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "query": query,
            "search_depth": os.getenv("TAVILY_SEARCH_DEPTH", "basic"),
            "max_results": limit,
            "include_answer": False,
            "include_raw_content": False,
        }
        if domain:
            payload["include_domains"] = [domain]
        try:
            r = self.session.post(
                "https://api.tavily.com/search",
                json=payload,
                headers={"Authorization": f"Bearer {self.tavily_key}"},
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as exc:
            raise WebError(f"Falha na busca Tavily: {exc}") from exc
        return [
            WebResult(
                title=str(x.get("title") or x.get("url") or "Resultado"),
                url=str(x.get("url") or ""),
                content=str(x.get("content") or "")[: self.max_content_chars],
                score=float(x["score"]) if x.get("score") is not None else None,
                source="tavily",
                published_date=x.get("published_date"),
            ).to_dict()
            for x in data.get("results", [])
            if x.get("url")
        ]

    def _tavily_extract(self, url: str, query: str | None) -> dict[str, Any]:
        payload: dict[str, Any] = {"urls": [url], "extract_depth": "basic", "format": "markdown"}
        if query:
            payload["query"] = query
            payload["chunks_per_source"] = 4
        try:
            r = self.session.post(
                "https://api.tavily.com/extract",
                json=payload,
                headers={"Authorization": f"Bearer {self.tavily_key}"},
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as exc:
            raise WebError(f"Falha na extração Tavily: {exc}") from exc
        result = (data.get("results") or [{}])[0]
        return {"url": url, "title": self._title_from_url(url), "content": str(result.get("raw_content") or "")[: self.max_content_chars], "source": "tavily"}

    def _brave_search(self, query: str, limit: int, domain: str | None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"q": query, "count": limit, "search_lang": "pt-br", "country": "br"}
        if domain:
            params["site"] = domain
        try:
            r = self.session.get(
                "https://api.search.brave.com/res/v1/web/search",
                params=params,
                headers={"Accept": "application/json", "X-Subscription-Token": self.brave_key},
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as exc:
            raise WebError(f"Falha na busca Brave: {exc}") from exc
        results = data.get("web", {}).get("results", [])
        return [
            WebResult(
                title=str(x.get("title") or x.get("url") or "Resultado"),
                url=str(x.get("url") or ""),
                content=str(x.get("description") or "")[: self.max_content_chars],
                source="brave",
            ).to_dict()
            for x in results
            if x.get("url")
        ]

    def _direct_open(self, url: str) -> dict[str, Any]:
        try:
            r = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            r.raise_for_status()
        except requests.RequestException as exc:
            raise WebError(f"Falha ao abrir URL: {exc}") from exc
        content_type = r.headers.get("Content-Type", "")
        if "text" not in content_type and "json" not in content_type and "xml" not in content_type:
            raise WebError("A URL não retornou conteúdo textual compatível.")
        text = re.sub(r"\s+", " ", r.text).strip()
        return {"url": r.url, "title": self._title_from_url(r.url), "content": text[: self.max_content_chars], "source": "direct"}

    @staticmethod
    def _title_from_url(url: str) -> str:
        return urlparse(url).netloc or url
