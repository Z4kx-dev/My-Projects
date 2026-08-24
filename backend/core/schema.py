"""Validação de contratos JSON da plataforma."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"


def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_world(data: dict[str, Any]) -> None:
    schema = load_schema("mundo.schema.json")
    resolver = RefResolver((SCHEMA_DIR / "mundo.schema.json").as_uri(), schema)
    Draft202012Validator(schema, resolver=resolver).validate(data)
