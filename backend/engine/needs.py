from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Needs:
    fome: float = 0.0
    sede: float = 0.0
    sono: float = 0.0
    fadiga: float = 0.0
    dor: float = 0.0
    estresse: float = 0.0

    def advance(self, minutes: int) -> None:
        factor = max(0.0, minutes / 60.0)
        self.fome = min(100.0, self.fome + 1.0 * factor)
        self.sede = min(100.0, self.sede + 1.3 * factor)
        self.sono = min(100.0, self.sono + 0.6 * factor)
        self.fadiga = min(100.0, self.fadiga + 0.5 * factor)

    def sleep(self, minutes: int) -> None:
        factor = max(0.0, minutes / 60.0)
        self.sono = max(0.0, self.sono - 8.0 * factor)
        self.fadiga = max(0.0, self.fadiga - 6.0 * factor)
