"""Tests for patchwork.notifier."""

import json
import os

import pytest

from patchwork.config import Step
from patchwork.executor import ExecutionReport, StepResult
from patchwork.notifier import build_summary, write_summary, maybe_write_summary


def _make_report(success: bool) -> ExecutionReport:
    step = Step(name="build", run="make")
    sr = StepResult(step=step, returncode=0 if success else 1, stdout="out", skipped=False)
    return ExecutionReport(
        results=[sr],
        success=success,
        failed_step=None if success else "build",
    )


def test_build_summary_success():
    report = _make_report(True)
    summary = build_summary(report, "my-pipeline")
    assert summary["pipeline"] == "my-pipeline"
    assert summary["success"] is True
    assert summary["failed_step"] is None
    assert len(summary["steps"]) == 1
    assert summary["steps"][0]["name"] == "build"


def test_build_summary_failure():
    report = _make_report(False)
    summary = build_summary(report, "ci")
    assert summary["success"] is False
    assert summary["failed_step"] == "build"


def test_build_summary_has_timestamp():
    summary = build_summary(_make_report(True), "p")
    assert "timestamp" in summary
    assert summary["timestamp"].endswith("+00:00")


def test_write_summary_creates_file(tmp_path):
    out = tmp_path / "reports" / "result.json"
    write_summary(_make_report(True), "pipe", str(out))
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["pipeline"] == "pipe"


def test_maybe_write_summary_skips_when_none(tmp_path):
    maybe_write_summary(_make_report(True), "pipe", None)
    assert list(tmp_path.iterdir()) == []


def test_maybe_write_summary_writes_when_path_given(tmp_path):
    out = str(tmp_path / "out.json")
    maybe_write_summary(_make_report(False), "pipe", out)
    assert os.path.exists(out)
