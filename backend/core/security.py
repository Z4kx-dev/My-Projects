from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthConfig:
    enabled: bool = False
    token_ttl: int = 86400


def config() -> AuthConfig:
    return AuthConfig(enabled=os.getenv("RPG_AUTH_ENABLED", "0").lower() in {"1", "true", "yes"}, token_ttl=max(300, int(os.getenv("RPG_TOKEN_TTL", "86400"))))


def issue_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    salt = os.getenv("RPG_AUTH_SALT", "change-me")
    return hashlib.sha256((salt + token).encode()).hexdigest()


def constant_time_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def valid_bearer(auth_header: str | None, expected_hash: str | None) -> bool:
    cfg = config()
    if not cfg.enabled:
        return True
    if not auth_header or not auth_header.startswith("Bearer ") or not expected_hash:
        return False
    return constant_time_equal(hash_token(auth_header[7:].strip()), expected_hash)


class RateLimiter:
    def __init__(self, limit: int = 120, window: int = 60):
        self.limit, self.window = max(1, limit), max(1, window)
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = [t for t in self._hits.get(key, []) if now - t < self.window]
        if len(hits) >= self.limit:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True
