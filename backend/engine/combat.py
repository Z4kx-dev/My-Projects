from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Combatant:
    name: str
    forca: float = 50.0
    agilidade: float = 50.0
    velocidade: float = 50.0
    resistencia: float = 50.0
    tecnica: float = 50.0
    moral: float = 50.0
    fadiga: float = 0.0
    integridade: float = 100.0


def estimate_advantage(attacker: Combatant, defender: Combatant) -> float:
    atk = (attacker.forca * .30 + attacker.agilidade * .20 + attacker.velocidade * .15 + attacker.tecnica * .25 + attacker.moral * .10)
    deff = (defender.agilidade * .25 + defender.velocidade * .20 + defender.resistencia * .25 + defender.tecnica * .20 + defender.moral * .10)
    atk *= max(.1, 1 - attacker.fadiga / 125)
    deff *= max(.1, 1 - defender.fadiga / 125)
    return atk / max(1.0, deff)
