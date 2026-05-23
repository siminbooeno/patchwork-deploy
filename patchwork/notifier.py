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
    """Write JSON summary to *output_path*, creating parent dirs as needed.

    Raises:
        OSError: If the file cannot be written (e.g. permission denied).
    """
    summary = build_summary(report, pipeline_name)
    abs_path = os.path.abspath(output_path)
    parent_dir = os.path.dirname(abs_path)
    try:
        os.makedirs(parent_dir, exist_ok=True)
    except OSError as exc:
        raise OSError(
            f"Failed to create output directory '{parent_dir}': {exc}"
        ) from exc
    try:
        with open(abs_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
    except OSError as exc:
        raise OSError(
            f"Failed to write summary to '{abs_path}': {exc}"
        ) from exc


def read_summary(input_path: str) -> dict:
    """Read and parse a JSON summary file previously written by :func:`write_summary`.

    Args:
        input_path: Path to the JSON summary file.

    Returns:
        The parsed summary as a dictionary.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If the file does not contain valid JSON.
    """
    abs_path = os.path.abspath(input_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as exc:
        raise OSError(f"Failed to read summary from '{abs_path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in summary file '{abs_path}': {exc}") from exc


def maybe_write_summary(
    report: ExecutionReport,
    pipeline_name: str,
    output_path: Optional[str],
) -> None:
    """Write summary only when *output_path* is not None/empty."""
    if output_path:
        write_summary(report, pipeline_name, output_path)
