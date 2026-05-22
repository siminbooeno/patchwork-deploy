"""Rollback support: run rollback steps when a pipeline stage fails."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

from patchwork.config import Step
from patchwork.executor import StepResult


@dataclass
class RollbackResult:
    step_name: str
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


@dataclass
class RollbackReport:
    triggered_by: str  # name of the step that caused the rollback
    results: List[RollbackResult] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        return all(r.success for r in self.results)


def run_rollback_step(
    step: Step, dry_run: bool = False
) -> RollbackResult:
    """Execute a single rollback step, respecting dry_run mode."""
    if dry_run:
        return RollbackResult(
            step_name=step.name,
            success=True,
            stdout="[dry-run] skipped",
        )
    try:
        proc = subprocess.run(
            step.run,
            shell=True,
            capture_output=True,
            text=True,
            cwd=step.workdir,
            env=step.env or None,
        )
        return RollbackResult(
            step_name=step.name,
            success=proc.returncode == 0,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            returncode=proc.returncode,
        )
    except Exception as exc:  # noqa: BLE001
        return RollbackResult(
            step_name=step.name,
            success=False,
            stderr=str(exc),
            returncode=1,
        )


def run_rollback(
    rollback_steps: List[Step],
    triggered_by: str,
    dry_run: bool = False,
) -> Optional[RollbackReport]:
    """Run all rollback steps and return a RollbackReport, or None if list is empty."""
    if not rollback_steps:
        return None
    report = RollbackReport(triggered_by=triggered_by)
    for step in rollback_steps:
        result = run_rollback_step(step, dry_run=dry_run)
        report.results.append(result)
    return report
