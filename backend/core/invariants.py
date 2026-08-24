from __future__ import annotations

from typing import Any


def check_world_invariants(world: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not world.get("id"): errors.append("mundo sem id")
    if not isinstance(world.get("entidades", []), list): errors.append("entidades deve ser lista")
    if not isinstance(world.get("eventos", []), list): errors.append("eventos deve ser lista")
    tempo = world.get("tempo", {})
    if not isinstance(tempo, dict): errors.append("tempo deve ser objeto")
    economia = world.get("economia", {})
    if not isinstance(economia, dict): errors.append("economia deve ser objeto")
    seen: set[str] = set()
    for entity in world.get("entidades", []):
        if not isinstance(entity, dict):
            errors.append("entidade inválida")
            continue
        eid = str(entity.get("id", ""))
        if not eid: errors.append("entidade sem id")
        if eid in seen: errors.append(f"entidade duplicada: {eid}")
        seen.add(eid)
        needs = entity.get("necessidades", entity.get("needs", {}))
        if isinstance(needs, dict):
            for key, value in needs.items():
                if isinstance(value, (int, float)) and not 0 <= value <= 100:
                    errors.append(f"necessidade fora do intervalo: {eid}.{key}")
    return errors
