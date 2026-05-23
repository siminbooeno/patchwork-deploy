"""Step timeout support — enforce per-step wall-clock limits."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TimeoutPolicy:
    """Resolved timeout settings for a single step."""
    seconds: Optional[float]  # None means no limit

    @property
    def enabled(self) -> bool:
        return self.seconds is not None


def parse_timeout(raw: object) -> TimeoutPolicy:
    """Parse the *timeout* field from a step definition.

    Accepted forms:
      - absent / null  → no timeout
      - integer / float → seconds
      - string like "30s", "2m", "1.5h"
    """
    if raw is None:
        return TimeoutPolicy(seconds=None)
    if isinstance(raw, (int, float)):
        if raw <= 0:
            raise ValueError(f"timeout must be positive, got {raw!r}")
        return TimeoutPolicy(seconds=float(raw))
    if isinstance(raw, str):
        return TimeoutPolicy(seconds=_parse_duration(raw))
    raise TypeError(f"timeout must be a number or duration string, got {type(raw).__name__!r}")


def _parse_duration(text: str) -> float:
    """Convert a human-readable duration string to seconds."""
    text = text.strip()
    multipliers = {"s": 1, "m": 60, "h": 3600}
    for suffix, factor in multipliers.items():
        if text.endswith(suffix):
            value_str = text[:-1]
            try:
                value = float(value_str)
            except ValueError:
                raise ValueError(f"invalid timeout string: {text!r}") from None
            if value <= 0:
                raise ValueError(f"timeout must be positive, got {text!r}")
            return value * factor
    # bare number string
    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"invalid timeout string: {text!r}") from None
    if value <= 0:
        raise ValueError(f"timeout must be positive, got {text!r}")
    return value


@dataclass
class TimeoutReport:
    """Summary of timeout outcomes across a pipeline run."""
    timed_out_steps: list[str] = field(default_factory=list)

    @property
    def any_timed_out(self) -> bool:
        return bool(self.timed_out_steps)

    def record_timeout(self, step_name: str) -> None:
        self.timed_out_steps.append(step_name)

    def as_dict(self) -> dict:
        return {
            "any_timed_out": self.any_timed_out,
            "timed_out_steps": list(self.timed_out_steps),
        }


def apply_timeout(
    proc: "subprocess.Popen[str]",
    policy: TimeoutPolicy,
    step_name: str,
    report: TimeoutReport,
) -> tuple[str, int]:
    """Wait for *proc* to finish, enforcing *policy*.

    Returns (stdout_text, returncode).  If the process exceeds the
    timeout it is killed, the step is recorded in *report*, and a
    non-zero return code (-1) is returned.
    """
    timeout = policy.seconds if policy.enabled else None
    try:
        stdout, _ = proc.communicate(timeout=timeout)
        return stdout, proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()  # drain
        report.record_timeout(step_name)
        return f"[timeout after {policy.seconds}s]", -1
