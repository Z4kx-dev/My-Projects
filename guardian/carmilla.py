"""Carmilla 3.1 — guardião da memória persistente do RPG Simulator."""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from datetime import datetime, timezone


WORLD_RE = re.compile(r"^(?:(real|fantasia):)?\d{3}$")
CATEGORIES = ("personagem", "npcs", "politica", "economia", "diario", "eventos")


class UpdateValidator:
    _allowed_categories = set(CATEGORIES)

    def validate_updates(self, updates):
        valid, rejected = [], []
        if not isinstance(updates, list):
            return [], [{"update": updates, "reason": "updates não é uma lista"}]
        for update in updates:
            if not isinstance(update, dict):
                rejected.append({"update": update, "reason": "alteração não é objeto"})
                continue
            file_path = update.get("file")
            changes = update.get("changes")
            if not isinstance(file_path, str) or not isinstance(changes, dict):
                rejected.append({"update": update, "reason": "file/changes inválidos"})
                continue
            normalized = file_path.replace("\\", "/").strip("/")
            if normalized.startswith("../") or "/../" in normalized or normalized == ".." or normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
                rejected.append({"update": update, "reason": "caminho inseguro"})
                continue
            category = normalized.split("/", 1)[0]
            if category not in self._allowed_categories or not normalized.endswith(".json"):
                rejected.append({"update": update, "reason": "arquivo/categoria não permitidos"})
                continue
            valid.append({"file": normalized, "changes": deepcopy(changes)})
        return valid, rejected


class MemoryStore:
    def __init__(self, worlds_dir):
        self.worlds_dir = os.path.abspath(worlds_dir)

    def _world_dir(self, world_id):
        world_id = str(world_id)
        if not WORLD_RE.fullmatch(world_id):
            raise ValueError("ID de mundo inválido")
        if ":" in world_id:
            tipo, numero = world_id.split(":", 1)
            return os.path.join(self.worlds_dir, tipo, numero)
        return os.path.join(self.worlds_dir, world_id)

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _merge(target, changes):
        for key, value in changes.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                MemoryStore._merge(target[key], value)
            else:
                target[key] = value

    def apply_updates(self, world_id, updates):
        root = self._world_dir(world_id)
        applied = []
        for update in updates:
            relative = update["file"]
            path = os.path.abspath(os.path.join(root, relative))
            if os.path.commonpath([root, path]) != root:
                continue
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

    def snapshot(self, world_id):
        root = self._world_dir(world_id)
        result = {}
        if not os.path.isdir(root):
            return result
        for category in CATEGORIES:
            folder = os.path.join(root, category)
            if not os.path.isdir(folder):
                continue
            result[category] = {}
            for base, _, files in os.walk(folder):
                for filename in files:
                    if not filename.endswith(".json"):
                        continue
                    path = os.path.join(base, filename)
                    rel = os.path.relpath(path, folder).replace(os.sep, "/")
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            result[category][rel] = json.load(f)
                    except (OSError, json.JSONDecodeError):
                        pass
        return result


class Carmilla:
    NAME = "Carmilla"
    VERSION = "3.1"

    def __init__(self, worlds_dir):
        self.worlds_dir = os.path.abspath(worlds_dir)
        self.validator = UpdateValidator()
        self.memory = MemoryStore(self.worlds_dir)

    def ensure_world(self, world_id):
        root = self.memory._world_dir(world_id)
        os.makedirs(root, exist_ok=True)
        for category in ("chat", *CATEGORIES, "historico"):
            os.makedirs(os.path.join(root, category), exist_ok=True)
        return world_id

    def status(self):
        return {"name": self.NAME, "version": self.VERSION, "active": True, "worlds_dir": self.worlds_dir}

    def get_memory(self, world_id):
        self.ensure_world(world_id)
        return self.memory.snapshot(world_id)
