from __future__ import annotations

import os
from flask import Flask, jsonify, request

from .security import RateLimiter, hash_token, valid_bearer


def install(app: Flask) -> None:
    """Instala autenticação opcional e rate limit global sem quebrar dev local."""
    limiter = RateLimiter(
        limit=max(1, int(os.getenv("RPG_RATE_LIMIT", "120"))),
        window=max(1, int(os.getenv("RPG_RATE_WINDOW", "60"))),
    )
    expected_hash = os.getenv("RPG_AUTH_TOKEN_HASH", "").strip() or None

    @app.before_request
    def _security_guard():
        if request.path.startswith("/static/") or request.path == "/":
            return None
        key = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
        if not limiter.allow(key):
            return jsonify({"error": "Limite de requisições excedido. Tente novamente em instantes."}), 429
        if not valid_bearer(request.headers.get("Authorization"), expected_hash):
            return jsonify({"error": "Autenticação necessária."}), 401
        return None
