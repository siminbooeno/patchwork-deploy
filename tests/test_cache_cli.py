"""Tests for patchwork.cache_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from patchwork.config import Step
from patchwork.step_cache import StepCache
from patchwork.cache_cli import (
    build_cache_parser,
    cmd_clear,
    cmd_export,
    cmd_invalidate,
    cmd_show,
)


def _step(name: str = "build", command: str = "make") -> Step:
    return Step(name=name, command=command, tags=[], rollback=None, allow_failure=False, retry=None)


def _populate(tmp_path: Path) -> Path:
    p = tmp_path / "cache.json"
    cache = StepCache(path=p)
    cache.record(_step("build", "make"), exit_code=0)
    cache.record(_step("test", "pytest"), exit_code=0)
    cache.save()
    return p


def _args(cache_file: str, **kwargs) -> argparse.Namespace:
    ns = argparse.Namespace(cache_file=cache_file)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


# ---------------------------------------------------------------------------

def test_show_empty(tmp_path, capsys):
    p = tmp_path / "empty.json"
    rc = cmd_show(_args(str(p)))
    assert rc == 0
    assert "empty" in capsys.readouterr().out


def test_show_entries(tmp_path, capsys):
    p = _populate(tmp_path)
    rc = cmd_show(_args(str(p)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "build" in out
    assert "test" in out


def test_clear_removes_entries(tmp_path, capsys):
    p = _populate(tmp_path)
    rc = cmd_clear(_args(str(p)))
    assert rc == 0
    loaded = StepCache.load(p)
    assert loaded._entries == {}


def test_clear_missing_file(tmp_path, capsys):
    p = tmp_path / "no.json"
    rc = cmd_clear(_args(str(p)))
    assert rc == 0
    assert "Nothing" in capsys.readouterr().out


def test_invalidate_existing(tmp_path, capsys):
    p = _populate(tmp_path)
    rc = cmd_invalidate(_args(str(p), step="build"))
    assert rc == 0
    loaded = StepCache.load(p)
    assert "build" not in loaded._entries
    assert "test" in loaded._entries


def test_invalidate_missing_step(tmp_path, capsys):
    p = _populate(tmp_path)
    rc = cmd_invalidate(_args(str(p), step="nonexistent"))
    assert rc == 1


def test_export_json(tmp_path, capsys):
    p = _populate(tmp_path)
    rc = cmd_export(_args(str(p)))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "build" in data
    assert "test" in data


def test_build_cache_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    build_cache_parser(sub)
    args = parser.parse_args(["cache", "show"])
    assert args.cache_cmd == "show"
