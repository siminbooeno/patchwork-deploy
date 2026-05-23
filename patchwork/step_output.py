"""Capture and store per-step stdout/stderr output with optional truncation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

_DEFAULT_MAX_LINES = 200


@dataclass
class StepOutput:
    step_name: str
    stdout_lines: List[str] = field(default_factory=list)
    stderr_lines: List[str] = field(default_factory=list)
    truncated: bool = False

    @property
    def stdout(self) -> str:
        return "\n".join(self.stdout_lines)

    @property
    def stderr(self) -> str:
        return "\n".join(self.stderr_lines)

    def has_output(self) -> bool:
        return bool(self.stdout_lines or self.stderr_lines)

    def as_dict(self) -> dict:
        return {
            "step": self.step_name,
            "stdout": self.stdout_lines,
            "stderr": self.stderr_lines,
            "truncated": self.truncated,
        }


def capture_output(
    step_name: str,
    raw_stdout: str,
    raw_stderr: str,
    max_lines: int = _DEFAULT_MAX_LINES,
) -> StepOutput:
    """Split raw output strings into lines and apply optional truncation."""
    stdout_lines = raw_stdout.splitlines() if raw_stdout else []
    stderr_lines = raw_stderr.splitlines() if raw_stderr else []

    total = len(stdout_lines) + len(stderr_lines)
    truncated = total > max_lines

    if truncated:
        # Allocate budget proportionally
        if stdout_lines and stderr_lines:
            half = max_lines // 2
            stdout_lines = stdout_lines[:half]
            stderr_lines = stderr_lines[: max_lines - half]
        elif stdout_lines:
            stdout_lines = stdout_lines[:max_lines]
        else:
            stderr_lines = stderr_lines[:max_lines]

    return StepOutput(
        step_name=step_name,
        stdout_lines=stdout_lines,
        stderr_lines=stderr_lines,
        truncated=truncated,
    )


def format_output(output: StepOutput, indent: str = "  ") -> str:
    """Return a human-readable string representation of captured output."""
    lines: List[str] = []
    if output.stdout_lines:
        lines.append(f"{indent}[stdout]")
        for ln in output.stdout_lines:
            lines.append(f"{indent}  {ln}")
    if output.stderr_lines:
        lines.append(f"{indent}[stderr]")
        for ln in output.stderr_lines:
            lines.append(f"{indent}  {ln}")
    if output.truncated:
        lines.append(f"{indent}  ... (output truncated)")
    return "\n".join(lines)
