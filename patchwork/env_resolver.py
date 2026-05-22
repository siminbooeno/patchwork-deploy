"""Resolve environment variable references in step commands and configs."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}")


@dataclass
class ResolutionError(Exception):
    """Raised when a required environment variable is missing."""
    variable: str

    def __str__(self) -> str:
        return f"Required environment variable '{self.variable}' is not set"


def resolve(template: str, env: Optional[dict[str, str]] = None) -> str:
    """Expand ${VAR} and ${VAR:default} references in *template*.

    Args:
        template: A string potentially containing ``${VAR}`` or
                  ``${VAR:default}`` placeholders.
        env: Mapping to use instead of ``os.environ`` (useful in tests).

    Returns:
        The string with all placeholders replaced.

    Raises:
        ResolutionError: If a variable has no default and is absent from *env*.
    """
    if env is None:
        env = dict(os.environ)

    def _replace(match: re.Match) -> str:
        var_name = match.group(1)
        default = match.group(2)  # None when no colon was present
        if var_name in env:
            return env[var_name]
        if default is not None:
            return default
        raise ResolutionError(var_name)

    return _ENV_PATTERN.sub(_replace, template)


def resolve_step_command(command: str, env: Optional[dict[str, str]] = None) -> str:
    """Convenience wrapper — resolve env vars inside a shell command string."""
    return resolve(command, env)


def resolve_dict(
    data: dict[str, str],
    env: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    """Return a new dict with all *values* resolved."""
    return {k: resolve(v, env) for k, v in data.items()}
