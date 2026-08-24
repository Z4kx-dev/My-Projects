from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any


class StorageError(RuntimeError):
    """Erro de infraestrutura de persistência."""


class StorageCorruptionError(StorageError):
    """Arquivo JSON existente, porém inválido ou ilegível."""


class JsonStore:
    """Persistência JSON com escrita atômica, locks e validação de caminhos."""

    _locks: dict[str, RLock] = {}
    _locks_guard = RLock()

    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, *parts: str) -> Path:
        p = self.root.joinpath(*parts).resolve()
        if self.root != p and self.root not in p.parents:
            raise ValueError("Caminho de persistência inválido")
        return p

    def _lock_for(self, p: Path) -> RLock:
        key = str(p)
        with self._locks_guard:
            return self._locks.setdefault(key, RLock())

    def read(self, *parts: str, default: Any = None) -> Any:
        p = self.path(*parts)
        lock = self._lock_for(p)
        with lock:
            try:
                with p.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError:
                return default
            except (OSError, json.JSONDecodeError) as exc:
                raise StorageCorruptionError(f"Falha ao ler persistência: {p}") from exc

    def write(self, data: Any, *parts: str) -> None:
        p = self.path(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        lock = self._lock_for(p)
        with lock:
            fd, tmp = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=str(p.parent))
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, p)
            except (OSError, TypeError, ValueError) as exc:
                raise StorageError(f"Falha ao gravar persistência: {p}") from exc
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)

    def delete(self, *parts: str) -> bool:
        p = self.path(*parts)
        lock = self._lock_for(p)
        with lock:
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
