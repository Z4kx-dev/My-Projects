from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    data_dir: str = os.getenv("RPG_DATA_DIR", "data")
    llm_base_url: str = os.getenv("RPG_LLM_BASE_URL", "http://localhost:11434")
    llm_model: str = os.getenv("RPG_LLM_MODEL", "llama3.2")
    max_context_items: int = int(os.getenv("RPG_MAX_CONTEXT_ITEMS", "24"))
    retrieval_limit: int = int(os.getenv("RPG_RETRIEVAL_LIMIT", "12"))
    simulation_tick_minutes: int = int(os.getenv("RPG_SIMULATION_TICK_MINUTES", "5"))
    audit_enabled: bool = os.getenv("RPG_AUDIT_ENABLED", "1") != "0"


settings = Settings()
