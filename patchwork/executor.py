"""Step executor: runs shell commands with dry-run and rollback support."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional

from patchwork.config import PipelineConfig, Step


@dataclass
class StepResult:
    step: Step
    returncode: int
    stdout: str
    stderr: str
    skipped: bool = False

    @property
    def success(self) -> bool:
        return self.skipped or self.returncode == 0


@dataclass
class ExecutionReport:
    pipeline_name: str
    dry_run: bool
    results: List[StepResult] = field(default_factory=list)
    rolled_back: bool = False

    @property
    def success(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def failed_step(self) -> Optional[StepResult]:
        for r in self.results:
            if not r.success:
                return r
        return None


def _run_command(command: str, workdir: Optional[str], timeout: int) -> StepResult:
    """Execute a single shell command and return its result."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=timeout,
        )
        return StepResult(
            step=None,  # type: ignore[arg-type]
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )
    except subprocess.TimeoutExpired:
        return StepResult(step=None, returncode=1, stdout="", stderr=f"Command timed out after {timeout}s")  # type: ignore[arg-type]


def run_pipeline(
    config: PipelineConfig,
    dry_run: bool = False,
    workdir: Optional[str] = None,
) -> ExecutionReport:
    """Run all steps in a pipeline; on failure attempt rollback."""
    report = ExecutionReport(pipeline_name=config.name, dry_run=dry_run)
    executed: List[StepResult] = []

    for step in config.steps:
        if dry_run:
            result = StepResult(step=step, returncode=0, stdout="", stderr="", skipped=True)
            report.results.append(result)
            continue

        raw = _run_command(step.command, workdir, step.timeout)
        raw.step = step
        report.results.append(raw)

        if not raw.success:
            if config.rollback_on_failure:
                _rollback(executed, workdir, report)
            return report

        executed.append(raw)

    return report


def _rollback(executed: List[StepResult], workdir: Optional[str], report: ExecutionReport) -> None:
    """Run rollback commands for already-completed steps in reverse order."""
    report.rolled_back = True
    for result in reversed(executed):
        if result.step.rollback:
            _run_command(result.step.rollback, workdir, result.step.timeout)
