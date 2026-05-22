"""Tests for patchwork.audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from patchwork.audit import (
    AuditEntry,
    build_entry,
    maybe_write_entry,
    read_entries,
    write_entry,
)
from patchwork.executor import ExecutionReport, StepResult


def _step_result(name: str, success: bool, duration: float = 0.1) -> StepResult:
    return StepResult(
        name=name,
        command="echo test",
        success=success,
        returncode=0 if success else 1,
        stdout="",
        stderr="",
        skipped=False,
        duration_seconds=duration,
    )


def _make_report(success: bool) -> ExecutionReport:
    results = [_step_result("build", True, 0.5), _step_result("deploy", success, 0.3)]
    failed = None if success else results[1]
    return ExecutionReport(results=results, success=success, failed_step=failed)


def test_build_entry_success():
    report = _make_report(True)
    entry = build_entry(report, "my-pipeline", dry_run=False)
    assert entry.pipeline == "my-pipeline"
    assert entry.success is True
    assert entry.steps_total == 2
    assert entry.steps_ok == 2
    assert entry.failed_step is None
    assert entry.dry_run is False
    assert entry.duration_seconds == pytest.approx(0.8, abs=1e-4)


def test_build_entry_failure():
    report = _make_report(False)
    entry = build_entry(report, "my-pipeline")
    assert entry.success is False
    assert entry.steps_ok == 1
    assert entry.failed_step == "deploy"


def test_build_entry_tags():
    report = _make_report(True)
    entry = build_entry(report, "pipe", tags=["production", "v2"])
    assert entry.tags == ["production", "v2"]


def test_write_and_read_entry(tmp_path):
    path = tmp_path / "audit.jsonl"
    report = _make_report(True)
    entry = build_entry(report, "pipe")
    write_entry(entry, path)
    assert path.exists()
    lines = path.read_text().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["pipeline"] == "pipe"


def test_multiple_entries_appended(tmp_path):
    path = tmp_path / "audit.jsonl"
    for _ in range(3):
        write_entry(build_entry(_make_report(True), "pipe"), path)
    entries = read_entries(path)
    assert len(entries) == 3


def test_read_entries_missing_file(tmp_path):
    assert read_entries(tmp_path / "missing.jsonl") == []


def test_maybe_write_entry_no_target(_make_report=_make_report):
    result = maybe_write_entry(_make_report(True), "pipe")
    assert result is None


def test_maybe_write_entry_with_path(tmp_path, monkeypatch):
    monkeypatch.delenv("PATCHWORK_AUDIT", raising=False)
    path = tmp_path / "audit.jsonl"
    result = maybe_write_entry(_make_report(True), "pipe", audit_file=str(path))
    assert result == path
    assert path.exists()


def test_maybe_write_entry_env_var(tmp_path, monkeypatch):
    path = tmp_path / "env-audit.jsonl"
    monkeypatch.setenv("PATCHWORK_AUDIT", str(path))
    result = maybe_write_entry(_make_report(False), "pipe")
    assert result == path
    entries = read_entries(path)
    assert entries[0].success is False
