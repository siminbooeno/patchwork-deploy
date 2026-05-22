"""Console output helpers for patchwork-deploy."""

from __future__ import annotations

from typing import Optional

from patchwork.executor import ExecutionReport, StepResult

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def _c(color: str, text: str) -> str:
    return f"{color}{text}{RESET}"


def print_banner(pipeline_name: str, dry_run: bool) -> None:
    mode = _c(YELLOW, "DRY-RUN") if dry_run else _c(CYAN, "LIVE")
    print(f"\n{BOLD}{'='*50}{RESET}")
    print(f"{BOLD}Pipeline : {pipeline_name}{RESET}  [{mode}]")
    print(f"{BOLD}{'='*50}{RESET}\n")


def print_step_result(result: StepResult, index: int) -> None:
    name = result.step.name
    if result.skipped:
        status = _c(YELLOW, "SKIP")
        print(f"  [{index}] {status}  {name}  (dry-run)")
        return

    if result.success:
        status = _c(GREEN, "OK  ")
    else:
        status = _c(RED, "FAIL")

    print(f"  [{index}] {status}  {name}")

    if result.stdout:
        for line in result.stdout.splitlines():
            print(f"         {line}")

    if not result.success and result.stderr:
        print(_c(RED, f"         stderr: {result.stderr}"))


def print_report(report: ExecutionReport) -> None:
    print()
    for i, result in enumerate(report.results, start=1):
        print_step_result(result, i)

    print(f"\n{BOLD}{'='*50}{RESET}")

    if report.success:
        print(_c(GREEN, f"  Pipeline '{report.pipeline_name}' completed successfully."))
    else:
        failed: Optional[StepResult] = report.failed_step
        step_name = failed.step.name if failed else "unknown"
        print(_c(RED, f"  Pipeline '{report.pipeline_name}' FAILED at step: {step_name}"))
        if report.rolled_back:
            print(_c(YELLOW, "  Rollback was executed."))

    print(f"{BOLD}{'='*50}{RESET}\n")
