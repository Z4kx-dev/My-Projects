from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Message:
    role: str
    content: str
    timestamp: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Memory:
    id: str
    world_id: str
    tipo: str
    conteudo: str
    importancia: float = 0.5
    tags: list[str] = field(default_factory=list)
    origem: str = "simulacao"
    criado_em: str = field(default_factory=utc_now)
    atualizado_em: str = field(default_factory=utc_now)
    valido: bool = True


@dataclass
class WorldState:
    id: str
    nome: str
    tipo: str = "real"
    descricao: str = ""
    versao: int = 1
    tempo: dict[str, Any] = field(default_factory=dict)
    entidades: dict[str, Any] = field(default_factory=dict)
    economia: dict[str, Any] = field(default_factory=dict)
    sociedade: dict[str, Any] = field(default_factory=dict)
    ambiente: dict[str, Any] = field(default_factory=dict)
    regras: dict[str, Any] = field(default_factory=dict)
    criado_em: str = field(default_factory=utc_now)
    atualizado_em: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Event:
    id: str
    world_id: str
    tipo: str
    descricao: str
    inicio: str
    fim: str | None = None
    entidades: list[str] = field(default_factory=list)
    consequencias: list[dict[str, Any]] = field(default_factory=list)
    origem: str = "motor"
    confirmado: bool = True
