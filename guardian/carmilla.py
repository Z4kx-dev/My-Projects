"""Carmilla: guardião da memória persistente do RPG Simulator.

A Carmilla não participa da narrativa. Ela valida e aplica apenas
alterações de memória produzidas pelo pipeline do backend.
"""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


class UpdateValidator:
    """Valida o formato básico das alterações antes de gravá-las."""

    _allowed_categories = {
        "personagem",
        "npcs",
        "politica",
        "economia",
        "diario",
        "eventos",
    }

    def validate_updates(self, updates: Any):
        valid = []
        rejected = []

        if not isinstance(updates, list):
            return [], [{"update": updates, "reason": "updates não é uma lista"}]

        for update in updates:
            if not isinstance(update, dict):
                rejected.append({"update": update, "reason": "alteração não é objeto"})
                continue

            file_path = update.get("file")
            changes = update.get("changes")

            if not isinstance(file_path, str) or not file_path.strip():
                rejected.append({"update": update, "reason": "file inválido"})
                continue

            if not isinstance(changes, dict):
                rejected.append({"update": update, "reason": "changes inválido"})
                continue

            normalized = file_path.replace("\\", "/").strip("/")

            # Bloqueia traversal e caminhos absolutos.
            if (
                normalized.startswith("../")
                or "/../" in normalized
                or normalized == ".."
                or normalized.startswith("/")
                or re.match(r"^[A-Za-z]:", normalized)
            ):
                rejected.append({"update": update, "reason": "caminho inseguro"})
                continue

            category = normalized.split("/", 1)[0]
            if category not in self._allowed_categories:
                rejected.append({"update": update, "reason": "categoria não permitida"})
                continue

            if not normalized.endswith(".json"):
                rejected.append({"update": update, "reason": "somente arquivos JSON são aceitos"})
                continue

            valid.append({
                "file": normalized,
                "changes": deepcopy(changes),
            })

        return valid, rejected


class MemoryStore:
    """Leitura e escrita atômica da memória categorizada de cada mundo."""

    def __init__(self, worlds_dir: str):
        self.worlds_dir = os.path.abspath(worlds_dir)

    def _world_dir(self, world_id: str) -> str:
        world_id = str(world_id)
        if not re.fullmatch(r"\d{3}", world_id):
            raise ValueError("ID de mundo inválido")
        return os.path.join(self.worlds_dir, world_id)

    def _path(self, world_id: str, relative_path: str) -> str:
        root = self._world_dir(world_id)
        path = os.path.abspath(os.path.join(root, relative_path))
        if os.path.commonpath([root, path]) != root:
            raise ValueError("Caminho fora do mundo")
        return path

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _merge(target: dict, changes: dict):
        for key, value in changes.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                MemoryStore._merge(target[key], value)
            else:
                target[key] = value

    def apply_updates(self, world_id: str, updates: list[dict]):
        applied = []

        for update in updates:
            relative = update["file"]
            path = self._path(world_id, relative)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except (OSError, json.JSONDecodeError):
                    data = {}
            else:
                data = {}

            if not isinstance(data, dict):
                data = {"data": data}

            self._merge(data, update["changes"])
            data["_carmilla_updated_at"] = self._now()

            temp = path + ".tmp"
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp, path)

            applied.append(relative)

        return applied

    def snapshot(self, world_id: str):
        root = self._world_dir(world_id)
        result = {}

        if not os.path.isdir(root):
            return result

        for category in (
            "personagem",
            "npcs",
            "politica",
            "economia",
            "diario",
            "eventos",
        ):
            category_dir = os.path.join(root, category)
            if not os.path.isdir(category_dir):
                continue

            result[category] = {}
            for base, _, files in os.walk(category_dir):
                for filename in files:
                    if not filename.endswith(".json"):
                        continue
                    path = os.path.join(base, filename)
                    rel = os.path.relpath(path, category_dir).replace(os.sep, "/")
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            result[category][rel] = json.load(f)
                    except (OSError, json.JSONDecodeError):
                        continue

        return result


class Carmilla:
    """Interface única usada pelo app.py para memória persistente."""

    VERSION = "3.1"
    NAME = "Carmilla"

    def __init__(self, worlds_dir: str):
        self.worlds_dir = os.path.abspath(worlds_dir)
        self.validator = UpdateValidator()
        self.memory = MemoryStore(self.worlds_dir)

    def ensure_world(self, world_id: str):
        world_dir = self.memory._world_dir(world_id)
        os.makedirs(world_dir, exist_ok=True)
        for category in (
            "chat",
            "personagem",
            "npcs",
            "politica",
            "economia",
            "diario",
            "eventos",
            "historico",
        ):
            os.makedirs(os.path.join(world_dir, category), exist_ok=True)
        return world_id

    def status(self):
        return {
            "name": self.NAME,
            "version": self.VERSION,
            "active": True,
            "worlds_dir": self.worlds_dir,
        }

    def get_memory(self, world_id: str):
        self.ensure_world(world_id)
        return self.memory.snapshot(world_id)
