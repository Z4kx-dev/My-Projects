from __future__ import annotations

from datetime import datetime, timedelta, timezone


class WorldClock:
    """Relógio monotônico de mundo: avanços são cumulativos e não retrocedem."""
    def __init__(self, value: str | None = None):
        self.value = self._parse(value) if value else datetime.now(timezone.utc)

    @staticmethod
    def _parse(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    def advance(self, seconds: int) -> str:
        if seconds < 0:
            raise ValueError("O tempo do mundo não pode retroceder")
        self.value += timedelta(seconds=int(seconds))
        return self.value.isoformat()

    def iso(self) -> str:
        return self.value.isoformat()
