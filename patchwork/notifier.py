"""Notification support: write a JSON summary file after pipeline execution."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

from patchwork.executor import ExecutionReport


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_summary(report: ExecutionReport, pipeline_name: str) -> dict:
    """Convert an ExecutionReport into a serialisable summary dict."""
    steps = []
    for sr in report.results:
        steps.append({
            "name": sr.step.name,
            "ok": sr.ok,
            "returncode": sr.returncode,
            "skipped": sr.skipped,
            "stdout": sr.stdout,
        })

    return {
        "pipeline": pipeline_name,
        "timestamp": _iso_now(),
        "success": report.success,
        "failed_step": report.failed_step,
        "steps": steps,
    }


def write_summary(
    report: ExecutionReport,
    pipeline_name: str,
    output_path: str,
) -> None:
    """Write JSON summary to *output_path*, creating parent dirs as needed."""
    summary = build_summary(report, pipeline_name)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")


def maybe_write_summary(
    report: ExecutionReport,
    pipeline_name: str,
    output_path: Optional[str],
) -> None:
    """Write summary only when *output_path* is not None/empty."""
    if output_path:
        write_summary(report, pipeline_name, output_path)
