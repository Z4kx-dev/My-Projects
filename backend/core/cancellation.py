from __future__ import annotations

from threading import Event


class CancellationToken:
    """Sinal compartilhado entre HTTP, agente e LLM durante uma execução."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def check(self) -> None:
        if self.cancelled:
            raise RuntimeError("Execução cancelada pelo usuário.")
