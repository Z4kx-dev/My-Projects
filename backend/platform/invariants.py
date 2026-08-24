from __future__ import annotations


def clamp(value: float, low: float, high: float) -> float:
    if low > high:
        raise ValueError("intervalo inválido")
    return max(low, min(high, value))


def require_non_negative(value: float, name: str = "valor") -> float:
    if value < 0:
        raise ValueError(f"{name} deve ser não negativo")
    return value


def require_probability(value: float, name: str = "probabilidade") -> float:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} deve estar entre 0 e 1")
    return value
