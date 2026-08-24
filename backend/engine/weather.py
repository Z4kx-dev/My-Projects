from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Weather:
    temperatura_c: float = 20.0
    umidade: float = 60.0
    vento_kmh: float = 5.0
    precipitacao: float = 0.0
    cobertura_nuvens: float = 30.0

    def advance(self, minutes: int) -> None:
        # Modelo deliberadamente simples e determinístico; substituível por um modelo climático posterior.
        drift = ((minutes % 37) - 18) / 100.0
        self.temperatura_c += drift
        self.temperatura_c = max(-60.0, min(60.0, self.temperatura_c))
        self.umidade = max(0.0, min(100.0, self.umidade - drift * 2))
