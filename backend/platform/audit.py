from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class AuditLog:
    """Log append-only de operações críticas, sem colocar estado no LLM."""

    def __init__(self, root: str | Path):
        self.path = Path(root) / "audit" / "events.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: str, payload: dict[str, Any] | None = None) -> None:
        row = {"ts": time.time(), "event": event, "payload": payload or {}}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
