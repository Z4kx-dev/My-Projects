from __future__ import annotations

import os
import time
from typing import Any


class HealthMonitor:
    def __init__(self) -> None:
        self.started = time.time()
        self.counters: dict[str, int] = {"requests": 0, "errors": 0, "llm_calls": 0, "tool_calls": 0}

    def request(self, error: bool = False) -> None:
        self.counters["requests"] += 1
        if error:
            self.counters["errors"] += 1

    def snapshot(self) -> dict[str, Any]:
        return {
            "uptime_seconds": round(time.time() - self.started, 2),
            "pid": os.getpid(),
            "counters": dict(self.counters),
        }
