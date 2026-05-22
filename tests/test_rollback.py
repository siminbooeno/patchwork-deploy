"""Tests for patchwork.rollback module."""
from __future__ import annotations

import pytest

from patchwork.config import Step
from patchwork.rollback import (
    RollbackReport,
    RollbackResult,
    run_rollback,
    run_rollback_step,
)


def _step(name: str, cmd: str) -> Step:
    return Step(name=name, run=cmd)


# ---------------------------------------------------------------------------
# run_rollback_step
# ---------------------------------------------------------------------------

def test_dry_run_returns_success_without_executing():
    step = _step("clean", "rm -rf /important")
    result = run_rollback_step(step, dry_run=True)
    assert result.success is True
    assert "dry-run" in result.stdout


def test_successful_command():
    step = _step("echo", "echo hello")
    result = run_rollback_step(step, dry_run=False)
    assert result.success is True
    assert result.returncode == 0
    assert "hello" in result.stdout


def test_failing_command():
    step = _step("fail", "exit 1")
    result = run_rollback_step(step, dry_run=False)
    assert result.success is False
    assert result.returncode != 0


def test_invalid_command_returns_failure():
    step = _step("bad", "__no_such_command_xyz__")
    result = run_rollback_step(step, dry_run=False)
    # shell=True means exit code non-zero but no exception
    assert result.success is False


# ---------------------------------------------------------------------------
# run_rollback
# ---------------------------------------------------------------------------

def test_run_rollback_empty_returns_none():
    result = run_rollback([], triggered_by="deploy")
    assert result is None


def test_run_rollback_dry_run_all_succeed():
    steps = [_step("r1", "exit 1"), _step("r2", "exit 2")]
    report = run_rollback(steps, triggered_by="deploy", dry_run=True)
    assert report is not None
    assert report.triggered_by == "deploy"
    assert len(report.results) == 2
    assert report.all_succeeded is True


def test_run_rollback_partial_failure():
    steps = [_step("ok", "echo ok"), _step("fail", "exit 42")]
    report = run_rollback(steps, triggered_by="build", dry_run=False)
    assert report is not None
    assert report.all_succeeded is False
    assert report.results[0].success is True
    assert report.results[1].success is False


def test_run_rollback_triggered_by_recorded():
    steps = [_step("cleanup", "echo cleanup")]
    report = run_rollback(steps, triggered_by="migrate", dry_run=False)
    assert report.triggered_by == "migrate"
