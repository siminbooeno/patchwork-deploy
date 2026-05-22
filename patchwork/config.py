"""Config loading and validation for patchwork-deploy."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


class ConfigError(ValueError):
    """Raised when the YAML config is invalid."""


@dataclass
class Step:
    name: str
    run: str
    workdir: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    ignore_errors: bool = False


@dataclass
class PipelineConfig:
    name: str
    steps: List[Step]
    rollback: List[Step] = field(default_factory=list)
    notify: Optional[Dict[str, Any]] = None
    hooks: Optional[Dict[str, Any]] = None


def _parse_step(raw: Any, index: int) -> Step:
    if isinstance(raw, str):
        return Step(name=f"step-{index}", run=raw)
    if not isinstance(raw, dict):
        raise ConfigError(f"Step {index} must be a string or mapping, got {type(raw)}")
    if "run" not in raw:
        raise ConfigError(f"Step {index} is missing required key 'run'")
    env_raw = raw.get("env")
    env: Optional[Dict[str, str]] = None
    if env_raw:
        env = {k: str(v) for k, v in env_raw.items()}
    return Step(
        name=raw.get("name", f"step-{index}"),
        run=raw["run"],
        workdir=raw.get("workdir"),
        env=env,
        ignore_errors=bool(raw.get("ignore_errors", False)),
    )


def _parse_steps(raw_list: Any, section: str) -> List[Step]:
    if not isinstance(raw_list, list):
        raise ConfigError(f"'{section}' must be a list")
    return [_parse_step(item, i) for i, item in enumerate(raw_list)]


def load_config(path: str) -> PipelineConfig:
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")
    with open(path, "r") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ConfigError("Config must be a YAML mapping")
    if "name" not in data:
        raise ConfigError("Config missing required key 'name'")
    if "steps" not in data:
        raise ConfigError("Config missing required key 'steps'")
    steps = _parse_steps(data["steps"], "steps")
    rollback: List[Step] = []
    if "rollback" in data:
        rollback = _parse_steps(data["rollback"], "rollback")
    return PipelineConfig(
        name=data["name"],
        steps=steps,
        rollback=rollback,
        notify=data.get("notify"),
        hooks=data.get("hooks"),
    )
