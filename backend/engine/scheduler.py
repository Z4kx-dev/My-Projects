from __future__ import annotations

from dataclasses import dataclass


@dataclass(order=True)
class ScheduledEvent:
    at_minute: int
    event_id: str
    payload: dict


class Scheduler:
    def __init__(self):
        self.events: list[ScheduledEvent] = []

    def schedule(self, at_minute: int, event_id: str, payload: dict | None = None) -> None:
        self.events.append(ScheduledEvent(at_minute, event_id, payload or {}))
        self.events.sort()

    def due(self, now_minute: int) -> list[ScheduledEvent]:
        due = [e for e in self.events if e.at_minute <= now_minute]
        self.events = [e for e in self.events if e.at_minute > now_minute]
        return due
