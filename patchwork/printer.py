"""Terminal output helpers for patchwork-deploy."""
from __future__ import annotations

from typing import Optional

from patchwork.executor import ExecutionReport, StepResult

# Import lazily to avoid circular at type-check time
try:
    from patchwork.rollback import RollbackReport
except ImportError:  # pragma: no cover
    RollbackReport = None  # type: ignore


ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "grey": "\033[90m",
}


def _c(text: str, *codes: str) -> str:
    prefix = "".join(ANSI[c] for c in codes)
    return f"{prefix}{text}{ANSI['reset']}"


def print_banner(name: str, dry_run: bool = False) -> None:
    tag = _c(" [DRY-RUN]", "yellow") if dry_run else ""
    print(_c(f"\n=== {name}{tag} ===", "bold", "cyan"))


def print_step_result(result: StepResult) -> None:
    icon = _c("✔", "green") if result.ok else _c("✘", "red")
    label = _c(result.step_name, "bold")
    print(f"  {icon}  {label}")
    if result.stdout:
        for line in result.stdout.splitlines():
            print(_c(f"      {line}", "grey"))
    if result.stderr:
        for line in result.stderr.splitlines():
            print(_c(f"      {line}", "red"))


def print_rollback_report(report: "RollbackReport") -> None:
    print(_c(f"\n--- Rollback triggered by: {report.triggered_by} ---", "yellow", "bold"))
    for r in report.results:
        icon = _c("✔", "green") if r.success else _c("✘", "red")
        label = _c(r.step_name, "bold")
        print(f"  {icon}  {label}")
        if r.stdout:
            for line in r.stdout.splitlines():
                print(_c(f"      {line}", "grey"))
        if r.stderr:
            for line in r.stderr.splitlines():
                print(_c(f"      {line}", "red"))
    status = _c("OK", "green") if report.all_succeeded else _c("FAILED", "red")
    print(_c(f"--- Rollback complete: {status} ---\n", "yellow"))


def print_report(report: ExecutionReport, rollback: Optional["RollbackReport"] = None) -> None:
    print()
    for step_result in report.results:
        print_step_result(step_result)
    if rollback is not None:
        print_rollback_report(rollback)
    if report.success:
        print(_c("\nPipeline succeeded.", "green", "bold"))
    else:
        print(_c(f"\nPipeline FAILED at step: {report.failed_step}", "red", "bold"))
