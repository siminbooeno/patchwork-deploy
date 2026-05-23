"""Step output caching — skip unchanged steps based on a content hash."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from patchwork.config import Step

_DEFAULT_CACHE_FILE = ".patchwork_cache.json"


@dataclass
class CacheEntry:
    step_name: str
    command_hash: str
    exit_code: int

    def as_dict(self) -> dict:
        return {
            "step_name": self.step_name,
            "command_hash": self.command_hash,
            "exit_code": self.exit_code,
        }

    @staticmethod
    def from_dict(d: dict) -> "CacheEntry":
        return CacheEntry(
            step_name=d["step_name"],
            command_hash=d["command_hash"],
            exit_code=d["exit_code"],
        )


@dataclass
class StepCache:
    path: Path
    _entries: Dict[str, CacheEntry] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    @staticmethod
    def load(path: str | Path = _DEFAULT_CACHE_FILE) -> "StepCache":
        p = Path(path)
        cache = StepCache(path=p)
        if p.exists():
            try:
                raw = json.loads(p.read_text())
                for key, val in raw.items():
                    cache._entries[key] = CacheEntry.from_dict(val)
            except (json.JSONDecodeError, KeyError):
                pass  # corrupt cache — start fresh
        return cache

    def save(self) -> None:
        self.path.write_text(
            json.dumps({k: v.as_dict() for k, v in self._entries.items()}, indent=2)
        )

    # ------------------------------------------------------------------
    def command_hash(self, step: Step) -> str:
        payload = step.command + "|".join(step.tags)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def is_cached(self, step: Step) -> bool:
        entry = self._entries.get(step.name)
        if entry is None:
            return False
        return entry.command_hash == self.command_hash(step) and entry.exit_code == 0

    def record(self, step: Step, exit_code: int) -> None:
        self._entries[step.name] = CacheEntry(
            step_name=step.name,
            command_hash=self.command_hash(step),
            exit_code=exit_code,
        )

    def invalidate(self, step_name: str) -> None:
        self._entries.pop(step_name, None)

    def clear(self) -> None:
        self._entries.clear()


def maybe_load_cache(enabled: bool, path: str = _DEFAULT_CACHE_FILE) -> Optional[StepCache]:
    """Return a StepCache if caching is enabled, else None."""
    if not enabled:
        return None
    return StepCache.load(path)
