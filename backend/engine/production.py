from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResourceStock:
    item: str
    quantity: float = 0.0
    capacity: float = 0.0

    def add(self, amount: float) -> float:
        if amount < 0:
            raise ValueError("amount deve ser >= 0")
        accepted = min(amount, max(0.0, self.capacity - self.quantity)) if self.capacity else amount
        self.quantity += accepted
        return accepted

    def remove(self, amount: float) -> float:
        if amount < 0 or amount > self.quantity:
            raise ValueError("estoque insuficiente")
        self.quantity -= amount
        return amount


@dataclass
class ProductionRecipe:
    name: str
    inputs: dict[str, float]
    outputs: dict[str, float]
    minutes: int


def can_produce(stock: dict[str, ResourceStock], recipe: ProductionRecipe, runs: int = 1) -> bool:
    return all(stock.get(k, ResourceStock(k)).quantity >= v * runs for k, v in recipe.inputs.items())
