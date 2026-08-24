from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class JsonStore:
    """Camada única de persistência. Escritas são atômicas e sempre UTF-8."""

    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, *parts: str) -> Path:
        p = (self.root.joinpath(*parts)).resolve()
        if self.root != p and self.root not in p.parents:
            raise ValueError("Caminho de persistência inválido")
        return p

    def read(self, *parts: str, default: Any = None) -> Any:
        p = self.path(*parts)
        try:
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return default

    def write(self, data: Any, *parts: str) -> None:
        p = self.path(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=str(p.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, p)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def delete(self, *parts: str) -> bool:
        p = self.path(*parts)
        try:
            p.unlink()
            return True
        except FileNotFoundError:
            return False

    def list_files(self, *parts: str, suffix: str = ".json") -> list[str]:
        p = self.path(*parts)
        if not p.exists():
            return []
        return sorted(x.name for x in p.iterdir() if x.is_file() and x.name.endswith(suffix))
