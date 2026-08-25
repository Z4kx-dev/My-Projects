from __future__ import annotations

import ipaddress
import os
import re
import socket
from dataclasses import asdict, dataclass
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
    """Cliente web sem API key obrigatória, com SearXNG local como padrão."""

    def __init__(self) -> None:
        self.provider = os.getenv("RPG_WEB_PROVIDER", "searxng").strip().lower()
        self.searxng_url = os.getenv("SEARXNG_URL", "http://127.0.0.1:8080").strip().rstrip("/")
        self.tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.brave_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
        self.timeout = max(3.0, float(os.getenv("RPG_WEB_TIMEOUT_SECONDS", "20")))
        self.max_results = min(20, max(1, int(os.getenv("RPG_WEB_MAX_RESULTS", "8"))))
        self.max_content_chars = min(50000, max(1000, int(os.getenv("RPG_WEB_MAX_CONTENT_CHARS", "12000"))))
        self.max_response_bytes = min(10_000_000, max(100_000, int(os.getenv("RPG_WEB_MAX_RESPONSE_BYTES", "3000000"))))
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": os.getenv("RPG_WEB_USER_AGENT", "KorczakAI/1.0")})

    @property
    def configured(self) -> bool:
        return self.provider == "searxng" or bool(self.tavily_key or self.brave_key)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.configured,
            "provider": self.provider,
            "searxng": self.provider == "searxng",
            "searxng_url": self.searxng_url,
            "tavily": bool(self.tavily_key),
            "brave": bool(self.brave_key),
        }

    def search(
        self,
        query: str,
        limit: int | None = None,
        domain: str | None = None,
        topic: str = "general",
        time_range: str | None = None,
    ) -> list[dict[str, Any]]:
        q = str(query or "").strip()
        if not q:
            raise WebError("A consulta web não pode ser vazia.")
        if len(q) > 400:
            raise WebError("A consulta web excede 400 caracteres.")
        topic = str(topic or "general").strip().lower()
        if topic not in {"general", "news"}:
            raise WebError("topic deve ser 'general' ou 'news'.")
        if time_range and str(time_range).lower() not in {"day", "week", "month", "year"}:
            raise WebError("time_range deve ser day, week, month ou year.")
        limit = min(self.max_results, max(1, int(limit or self.max_results)))

        if self.provider == "searxng":
            return self._searxng_search(q, limit, domain, topic, time_range)
        if self.provider == "brave" and self.brave_key:
            return self._brave_search(q, limit, domain, time_range)
        if self.provider == "tavily" and self.tavily_key:
            return self._tavily_search(q, limit, domain, topic, time_range)
        if self.tavily_key:
            return self._tavily_search(q, limit, domain, topic, time_range)
        if self.brave_key:
            return self._brave_search(q, limit, domain, time_range)
        raise WebError("Nenhum provedor web configurado.")

    def open(self, url: str, query: str | None = None) -> dict[str, Any]:
        self._validate_public_url(url)
        if self.tavily_key:
            try:
                return self._tavily_extract(url, query)
            except WebError:
                if self.provider == "tavily" and not self.brave_key:
                    raise
        return self._direct_open(url)

    def _searxng_search(self, query: str, limit: int, domain: str | None, topic: str, time_range: str | None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"q": query, "format": "json", "language": "pt-BR", "safesearch": 1, "categories": "news" if topic == "news" else "general"}
        if time_range:
            params["time_range"] = time_range
        if domain:
            clean_domain = domain.strip().removeprefix("https://").removeprefix("http://").split("/", 1)[0]
            if clean_domain:
                params["q"] = f"site:{clean_domain} {query}"
        try:
            r = self.session.get(f"{self.searxng_url}/search", params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as exc:
            raise WebError(f"Falha na busca SearXNG: {exc}") from exc
        results: list[dict[str, Any]] = []
        for item in data.get("results", [])[:limit]:
            url = str(item.get("url") or "").strip()
            if not url:
                continue
            results.append(WebResult(
                title=str(item.get("title") or url),
                url=url,
                content=str(item.get("content") or "")[: self.max_content_chars],
                score=float(item["score"]) if item.get("score") is not None else None,
                source="searxng",
                published_date=item.get("publishedDate") or item.get("published_date"),
            ).to_dict())
        return results

    def _tavily_search(self, query: str, limit: int, domain: str | None, topic: str, time_range: str | None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"query": query, "search_depth": os.getenv("TAVILY_SEARCH_DEPTH", "basic"), "max_results": limit, "include_answer": False, "include_raw_content": False, "topic": topic}
        if domain:
            payload["include_domains"] = [domain.strip()]
        if time_range:
            payload["time_range"] = time_range
        try:
            r = self.session.post("https://api.tavily.com/search", json=payload, headers={"Authorization": f"Bearer {self.tavily_key}"}, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as exc:
            raise WebError(f"Falha na busca Tavily: {exc}") from exc
        return [WebResult(title=str(x.get("title") or x.get("url") or "Resultado"), url=str(x.get("url") or ""), content=str(x.get("content") or "")[: self.max_content_chars], score=float(x["score"]) if x.get("score") is not None else None, source="tavily", published_date=x.get("published_date")).to_dict() for x in data.get("results", []) if x.get("url")]

    def _tavily_extract(self, url: str, query: str | None) -> dict[str, Any]:
        payload: dict[str, Any] = {"urls": [url], "extract_depth": "basic", "format": "markdown"}
        if query:
            payload["query"] = query
            payload["chunks_per_source"] = 4
        try:
            r = self.session.post("https://api.tavily.com/extract", json=payload, headers={"Authorization": f"Bearer {self.tavily_key}"}, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as exc:
            raise WebError(f"Falha na extração Tavily: {exc}") from exc
        result = (data.get("results") or [{}])[0]
        return {"url": url, "title": self._title_from_url(url), "content": str(result.get("raw_content") or "")[: self.max_content_chars], "source": "tavily"}

    def _brave_search(self, query: str, limit: int, domain: str | None, time_range: str | None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"q": query, "count": limit, "search_lang": "pt-br", "country": "br"}
        if domain:
            params["site"] = domain.strip()
        if time_range:
            params["freshness"] = {"day": "pd", "week": "pw", "month": "pm", "year": "py"}[time_range]
        try:
            r = self.session.get("https://api.search.brave.com/res/v1/web/search", params=params, headers={"Accept": "application/json", "X-Subscription-Token": self.brave_key}, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as exc:
            raise WebError(f"Falha na busca Brave: {exc}") from exc
        return [WebResult(title=str(x.get("title") or x.get("url") or "Resultado"), url=str(x.get("url") or ""), content=str(x.get("description") or "")[: self.max_content_chars], source="brave").to_dict() for x in data.get("web", {}).get("results", []) if x.get("url")]

    def _direct_open(self, url: str) -> dict[str, Any]:
        self._validate_public_url(url)
        try:
            r = self.session.get(url, timeout=self.timeout, allow_redirects=False, stream=True)
            r.raise_for_status()
            content_type = r.headers.get("Content-Type", "").lower()
            if "text" not in content_type and "json" not in content_type and "xml" not in content_type:
                raise WebError("A URL não retornou conteúdo textual compatível.")
            raw = bytearray()
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    raw.extend(chunk)
                    if len(raw) > self.max_response_bytes:
                        raise WebError("A resposta web excede o limite de tamanho permitido.")
            r.close()
        except requests.RequestException as exc:
            raise WebError(f"Falha ao abrir URL: {exc}") from exc
        if 300 <= r.status_code < 400:
            location = r.headers.get("Location")
            if not location:
                raise WebError("A página retornou um redirecionamento sem destino.")
            from urllib.parse import urljoin
            return self._direct_open(urljoin(url, location))
        text = raw.decode(r.encoding or "utf-8", errors="replace")
        text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<noscript[\s\S]*?</noscript>", " ", text, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return {"url": r.url, "title": self._title_from_url(r.url), "content": text[: self.max_content_chars], "source": "direct"}

    @staticmethod
    def _validate_public_url(url: str) -> None:
        parsed = urlparse(str(url).strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise WebError("URL inválida. Apenas HTTP/HTTPS são permitidos.")
        host = parsed.hostname.lower().rstrip(".")
        if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
            raise WebError("Acesso a localhost não é permitido pela ferramenta web.")
        try:
            addresses = {ipaddress.ip_address(host)}
        except ValueError:
            try:
                addresses = {ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
            except OSError as exc:
                raise WebError(f"Não foi possível resolver o domínio: {host}") from exc
        for address in addresses:
            if any((address.is_private, address.is_loopback, address.is_link_local, address.is_multicast, address.is_reserved, address.is_unspecified)):
                raise WebError("Acesso a endereço de rede interno ou reservado não é permitido.")

    @staticmethod
    def _title_from_url(url: str) -> str:
        return urlparse(url).netloc or url
