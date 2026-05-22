"""YAML configuration loader and validator for patchwork-deploy."""

import os
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class Step:
    name: str
    run: str
    rollback: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    ignore_errors: bool = False


@dataclass
class PipelineConfig:
    name: str
    steps: list[Step]
    env: dict[str, str] = field(default_factory=dict)
    working_dir: str = "."


class ConfigError(Exception):
    """Raised when the pipeline config is invalid."""


def _parse_step(raw: dict[str, Any]) -> Step:
    if "name" not in raw:
        raise ConfigError("Each step must have a 'name' field.")
    if "run" not in raw:
        raise ConfigError(f"Step '{raw['name']}' must have a 'run' field.")
    return Step(
        name=raw["name"],
        run=raw["run"],
        rollback=raw.get("rollback"),
        env=raw.get("env", {}),
        ignore_errors=bool(raw.get("ignore_errors", False)),
    )


def load_config(path: str) -> PipelineConfig:
    """Load and validate a pipeline YAML config file."""
    if not os.path.isfile(path):
        raise ConfigError(f"Config file not found: {path}")

    with open(path, "r") as fh:
        try:
            raw = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Failed to parse YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config must be a YAML mapping at the top level.")
    if "name" not in raw:
        raise ConfigError("Config must have a top-level 'name' field.")
    if "steps" not in raw or not isinstance(raw["steps"], list):
        raise ConfigError("Config must have a top-level 'steps' list.")

    steps = [_parse_step(s) for s in raw["steps"]]
    return PipelineConfig(
        name=raw["name"],
        steps=steps,
        env=raw.get("env", {}),
        working_dir=raw.get("working_dir", "."),
    )
