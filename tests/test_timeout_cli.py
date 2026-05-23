"""Tests for patchwork.timeout_cli."""
import json
import argparse
from pathlib import Path

import pytest

from patchwork.timeout_cli import cmd_timeouts, cmd_timeout_stats, build_timeout_parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_audit(path: Path, entries: list[dict]) -> None:
    with path.open("w") as fh:
        for e in entries:
            fh.write(json.dumps(e) + "\n")


def _args(audit_file: str) -> argparse.Namespace:
    return argparse.Namespace(audit_file=audit_file)


# ---------------------------------------------------------------------------
# cmd_timeouts
# ---------------------------------------------------------------------------

def test_timeouts_empty_file(tmp_path, capsys):
    f = tmp_path / "audit.jsonl"
    _write_audit(f, [])
    rc = cmd_timeouts(_args(str(f)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No timed-out" in out


def test_timeouts_no_timeouts(tmp_path, capsys):
    f = tmp_path / "audit.jsonl"
    _write_audit(f, [
        {"pipeline": "p", "timestamp": "t", "extra": {"any_timed_out": False}}
    ])
    rc = cmd_timeouts(_args(str(f)))
    assert rc == 0
    assert "No timed-out" in capsys.readouterr().out


def test_timeouts_with_hit(tmp_path, capsys):
    f = tmp_path / "audit.jsonl"
    _write_audit(f, [
        {
            "pipeline": "deploy",
            "timestamp": "2024-01-01T00:00:00Z",
            "extra": {"any_timed_out": True, "timed_out_steps": ["build"]},
        }
    ])
    rc = cmd_timeouts(_args(str(f)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "deploy" in out
    assert "build" in out


def test_timeouts_missing_file(tmp_path, capsys):
    rc = cmd_timeouts(_args(str(tmp_path / "missing.jsonl")))
    assert rc == 0
    assert "No timed-out" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# cmd_timeout_stats
# ---------------------------------------------------------------------------

def test_stats_empty(tmp_path, capsys):
    f = tmp_path / "audit.jsonl"
    _write_audit(f, [])
    rc = cmd_timeout_stats(_args(str(f)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "Total runs" in out
    assert "none" in out


def test_stats_counts(tmp_path, capsys):
    f = tmp_path / "audit.jsonl"
    _write_audit(f, [
        {"extra": {"any_timed_out": True, "timed_out_steps": ["build", "test"]}},
        {"extra": {"any_timed_out": True, "timed_out_steps": ["build"]}},
        {"extra": {"any_timed_out": False, "timed_out_steps": []}},
    ])
    rc = cmd_timeout_stats(_args(str(f)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "Total runs       : 3" in out
    assert "Runs with timeout: 2" in out
    assert "build: 2" in out
    assert "test: 1" in out


# ---------------------------------------------------------------------------
# build_timeout_parser wiring
# ---------------------------------------------------------------------------

def test_build_timeout_parser_registers_commands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    build_timeout_parser(sub)
    ns = parser.parse_args(["timeouts", "--audit-file", "x.jsonl"])
    assert ns.audit_file == "x.jsonl"
    assert hasattr(ns, "func")
