from __future__ import annotations

import json
import shutil
import time
from pathlib import Path


class SnapshotManager:
    def __init__(self, data_dir: str | Path):
        self.root = Path(data_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.snapshots = self.root / "snapshots"
        self.snapshots.mkdir(exist_ok=True)

    def create(self, world_id: str) -> str:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        target = self.snapshots / f"{world_id}-{stamp}"
        source = self.root / "worlds" / world_id
        if not source.exists():
            raise FileNotFoundError(world_id)
        shutil.copytree(source, target)
        return str(target)

    def restore(self, world_id: str, snapshot: str) -> None:
        source = Path(snapshot)
        target = self.root / "worlds" / world_id
        if not source.is_dir():
            raise FileNotFoundError(snapshot)
        replacement = target.with_name(target.name + ".restore")
        if replacement.exists():
            shutil.rmtree(replacement)
        shutil.copytree(source, replacement)
        if target.exists():
            shutil.rmtree(target)
        replacement.rename(target)
