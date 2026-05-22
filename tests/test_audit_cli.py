"""Tests for patchwork.audit_cli."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from patchwork.audit import build_entry, write_entry
from patchwork.audit_cli import build_audit_parser, run_audit_command
from patchwork.executor import ExecutionReport, StepResult


def _report(success: bool) -> ExecutionReport:
    r = StepResult(
        name="step", command="echo", success=success,
        returncode=0 if success else 1,
        stdout="", stderr="", skipped=False, duration_seconds=0.2,
    )
    return ExecutionReport(results=[r], success=success, failed_step=None if success else r)


def _populate(path: Path, n: int = 3) -> None:
    for i in range(n):
        write_entry(build_entry(_report(i % 2 == 0), f"pipe-{i}"), path)


def _parse(args_list):
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    build_audit_parser(subs)
    return parser.parse_args(args_list)


def test_list_empty(tmp_path, capsys):
    path = tmp_path / "audit.jsonl"
    args = _parse(["audit", "list", str(path)])
    rc = run_audit_command(args)
    assert rc == 0
    assert "No audit entries" in capsys.readouterr().out


def test_list_entries(tmp_path, capsys):
    path = tmp_path / "audit.jsonl"
    _populate(path, 2)
    args = _parse(["audit", "list", str(path)])
    rc = run_audit_command(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "pipe-0" in out
    assert "pipe-1" in out


def test_stats_output(tmp_path, capsys):
    path = tmp_path / "audit.jsonl"
    _populate(path, 4)
    args = _parse(["audit", "stats", str(path)])
    rc = run_audit_command(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Total runs" in out
    assert "Passed" in out
    assert "Failed" in out


def test_stats_empty(tmp_path, capsys):
    path = tmp_path / "empty.jsonl"
    args = _parse(["audit", "stats", str(path)])
    rc = run_audit_command(args)
    assert rc == 0
    assert "No audit entries" in capsys.readouterr().out


def test_export_valid_json(tmp_path, capsys):
    path = tmp_path / "audit.jsonl"
    _populate(path, 2)
    args = _parse(["audit", "export", str(path)])
    rc = run_audit_command(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) == 2
    assert "pipeline" in data[0]
