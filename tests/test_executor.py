"""Tests for patchwork.executor."""

from __future__ import annotations

import pytest

from patchwork.config import PipelineConfig, Step
from patchwork.executor import ExecutionReport, StepResult, run_pipeline


def _make_config(
    steps: list[Step],
    rollback_on_failure: bool = True,
    name: str = "test-pipeline",
) -> PipelineConfig:
    return PipelineConfig(name=name, steps=steps, rollback_on_failure=rollback_on_failure)


def _step(name: str, command: str, rollback: str | None = None, timeout: int = 30) -> Step:
    return Step(name=name, command=command, rollback=rollback, timeout=timeout)


# ---------------------------------------------------------------------------
# dry-run
# ---------------------------------------------------------------------------

def test_dry_run_skips_all_steps():
    config = _make_config([_step("echo", "echo hello"), _step("fail", "exit 1")])
    report = run_pipeline(config, dry_run=True)
    assert report.success
    assert report.dry_run
    assert all(r.skipped for r in report.results)
    assert not report.rolled_back


# ---------------------------------------------------------------------------
# successful execution
# ---------------------------------------------------------------------------

def test_successful_pipeline():
    config = _make_config([_step("true", "true"), _step("echo", "echo hi")])
    report = run_pipeline(config)
    assert report.success
    assert len(report.results) == 2
    assert not report.rolled_back


def test_stdout_captured():
    config = _make_config([_step("greet", "echo patchwork")])
    report = run_pipeline(config)
    assert report.results[0].stdout == "patchwork"


# ---------------------------------------------------------------------------
# failure & rollback
# ---------------------------------------------------------------------------

def test_failed_step_stops_pipeline():
    config = _make_config([
        _step("ok", "true"),
        _step("bad", "exit 42"),
        _step("never", "echo should-not-run"),
    ], rollback_on_failure=False)
    report = run_pipeline(config)
    assert not report.success
    assert len(report.results) == 2  # third step never executed
    assert report.failed_step.step.name == "bad"


def test_rollback_executed_on_failure(tmp_path):
    marker = tmp_path / "rolled_back.txt"
    config = _make_config([
        _step("step1", "true", rollback=f"touch {marker}"),
        _step("step2", "exit 1"),
    ])
    report = run_pipeline(config)
    assert not report.success
    assert report.rolled_back
    assert marker.exists()


def test_no_rollback_when_flag_off():
    config = _make_config(
        [_step("bad", "exit 1", rollback="echo should-not-run")],
        rollback_on_failure=False,
    )
    report = run_pipeline(config)
    assert not report.success
    assert not report.rolled_back


def test_timeout_causes_failure():
    config = _make_config([_step("slow", "sleep 10", timeout=1)])
    report = run_pipeline(config)
    assert not report.success
    assert "timed out" in report.results[0].stderr
