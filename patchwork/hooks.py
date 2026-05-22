"""Lifecycle hooks support for pipeline steps (on_success, on_failure, on_always)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

from patchwork.executor import StepResult


@dataclass
class HookResult:
    hook_type: str  # 'on_success' | 'on_failure' | 'on_always'
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass
class HookSet:
    on_success: List[str] = field(default_factory=list)
    on_failure: List[str] = field(default_factory=list)
    on_always: List[str] = field(default_factory=list)


def parse_hooks(raw: dict) -> HookSet:
    """Parse a hooks dict from YAML into a HookSet."""
    def _to_list(val) -> List[str]:
        if val is None:
            return []
        if isinstance(val, str):
            return [val]
        return list(val)

    return HookSet(
        on_success=_to_list(raw.get("on_success")),
        on_failure=_to_list(raw.get("on_failure")),
        on_always=_to_list(raw.get("on_always")),
    )


def run_hooks(
    hooks: HookSet,
    step_result: StepResult,
    dry_run: bool = False,
    timeout: Optional[int] = 30,
) -> List[HookResult]:
    """Run applicable hooks based on step result. Returns list of HookResults."""
    results: List[HookResult] = []

    candidates: List[tuple[str, List[str]]] = []
    if step_result.ok:
        candidates.append(("on_success", hooks.on_success))
    else:
        candidates.append(("on_failure", hooks.on_failure))
    candidates.append(("on_always", hooks.on_always))

    for hook_type, commands in candidates:
        for cmd in commands:
            if dry_run:
                results.append(HookResult(hook_type=hook_type, command=cmd,
                                          returncode=0, stdout="[dry-run]", stderr=""))
                continue
            try:
                proc = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=timeout
                )
                results.append(HookResult(
                    hook_type=hook_type,
                    command=cmd,
                    returncode=proc.returncode,
                    stdout=proc.stdout.strip(),
                    stderr=proc.stderr.strip(),
                ))
            except subprocess.TimeoutExpired:
                results.append(HookResult(
                    hook_type=hook_type, command=cmd,
                    returncode=-1, stdout="", stderr="timeout"
                ))
    return results
