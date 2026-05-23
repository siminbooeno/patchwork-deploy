"""Step gate: pause-and-confirm support for interactive pipeline runs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GatePolicy:
    enabled: bool = False
    message: str = "Continue?"
    timeout_seconds: Optional[float] = None  # None = wait forever


def is_gated(policy: GatePolicy) -> bool:
    return policy.enabled


def parse_gate(raw) -> GatePolicy:
    """Parse a 'gate' value from a step's YAML config.

    Accepted forms:
      gate: true                      -> enabled, default message
      gate: "Deploy to production?"   -> enabled, custom message
      gate:
        enabled: true
        message: "Are you sure?"
        timeout: 30
    """
    if raw is None or raw is False:
        return GatePolicy(enabled=False)
    if raw is True:
        return GatePolicy(enabled=True)
    if isinstance(raw, str):
        return GatePolicy(enabled=True, message=raw)
    if isinstance(raw, dict):
        enabled = bool(raw.get("enabled", True))
        message = str(raw.get("message", "Continue?"))
        timeout_raw = raw.get("timeout")
        timeout = float(timeout_raw) if timeout_raw is not None else None
        return GatePolicy(enabled=enabled, message=message, timeout_seconds=timeout)
    raise ValueError(f"Invalid gate value: {raw!r}")


def prompt_gate(policy: GatePolicy, *, _input=input) -> bool:
    """Prompt the user to confirm.  Returns True if confirmed, False if denied.

    The *_input* parameter exists so tests can inject a fake input function.
    """
    if not policy.enabled:
        return True
    prompt = f"[gate] {policy.message} [y/N] "
    try:
        answer = _input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("y", "yes")
