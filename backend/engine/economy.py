from __future__ import annotations

from typing import Any


class EconomyEngine:
    def __init__(self, world: dict[str, Any]):
        self.world = world
        self.world.setdefault("economia", {})
        self.world["economia"].setdefault("moeda", "unidade")
        self.world["economia"].setdefault("precos", {})
        self.world["economia"].setdefault("estoques", {})
        self.world["economia"].setdefault("tesouro", 0.0)

    def stock(self, resource: str, amount: float) -> float:
        current = float(self.world["economia"]["estoques"].get(resource, 0.0))
        updated = current + float(amount)
        if updated < 0:
            raise ValueError(f"Estoque insuficiente: {resource}")
        self.world["economia"]["estoques"][resource] = updated
        return updated

    def price(self, item: str, value: float) -> None:
        if value < 0:
            raise ValueError("Preço não pode ser negativo")
        self.world["economia"]["precos"][item] = float(value)

    def transact(self, buyer: dict[str, Any], seller: dict[str, Any], item: str, quantity: float) -> dict[str, Any]:
        if quantity <= 0:
            raise ValueError("Quantidade inválida")
        unit = float(self.world["economia"]["precos"].get(item, 0))
        total = unit * quantity
        if buyer.get("saldo", 0) < total:
            raise ValueError("Saldo insuficiente")
        buyer["saldo"] -= total
        seller["saldo"] = seller.get("saldo", 0) + total
        return {"item": item, "quantidade": quantity, "total": total}
