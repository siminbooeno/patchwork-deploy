"""YAML config loading and dataclasses for patchwork pipelines."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml

from patchwork.retry import RetryPolicy, parse_retry


class ConfigError(Exception):
    """Raised when the YAML config is malformed or missing."""


@dataclass
class Step:
    name: str
    command: str
    tags: List[str] = field(default_factory=list)
    rollback: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    retry: RetryPolicy = field(default_factory=RetryPolicy)


@dataclass
class PipelineConfig:
    name: str
    steps: List[Step]
    notify: Optional[str] = None
    audit_log: Optional[str] = None
    summary_file: Optional[str] = None


def _parse_step(raw: Any) -> Step:
    if not isinstance(raw, dict):
        raise ConfigError(f"Each step must be a mapping, got: {type(raw).__name__}")
    name = raw.get("name")
    command = raw.get("command")
    if not name:
        raise ConfigError("Step is missing required field 'name'")
    if not command:
        raise ConfigError(f"Step '{name}' is missing required field 'command'")
    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    env_raw = raw.get("env") or {}
    if not isinstance(env_raw, dict):
        raise ConfigError(f"Step '{name}' env must be a mapping")
    env = {k: str(v) for k, v in env_raw.items()}
    retry = parse_retry(raw.get("retry"))
    return Step(
        name=name,
        command=command,
        tags=list(tags),
        rollback=raw.get("rollback"),
        env=env,
        retry=retry,
    )


def _parse_steps(raw: Any) -> List[Step]:
    if not isinstance(raw, list):
        raise ConfigError("'steps' must be a list")
    return [_parse_step(s) for s in raw]


def load_config(path: str) -> PipelineConfig:
    """Load and parse a pipeline YAML file.

    Raises:
        ConfigError: if the file is missing or the content is invalid.
    """
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")
    with open(path, "r") as fh:
        try:
            data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ConfigError(f"YAML parse error: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Config must be a YAML mapping at the top level")
    name = data.get("pipeline")
    if not name:
        raise ConfigError("Config is missing required field 'pipeline'")
    steps = _parse_steps(data.get("steps", []))
    return PipelineConfig(
        name=name,
        steps=steps,
        notify=data.get("notify"),
        audit_log=data.get("audit_log"),
        summary_file=data.get("summary_file"),
    )
