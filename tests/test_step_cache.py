"""Tests for patchwork.step_cache."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from patchwork.config import Step
from patchwork.step_cache import CacheEntry, StepCache, maybe_load_cache


def _step(name: str = "deploy", command: str = "echo hello", tags=None) -> Step:
    return Step(name=name, command=command, tags=tags or [], rollback=None, allow_failure=False, retry=None)


# ---------------------------------------------------------------------------
# CacheEntry round-trip
# ---------------------------------------------------------------------------

def test_cache_entry_round_trip():
    entry = CacheEntry(step_name="s", command_hash="abc123", exit_code=0)
    restored = CacheEntry.from_dict(entry.as_dict())
    assert restored.step_name == "s"
    assert restored.command_hash == "abc123"
    assert restored.exit_code == 0


# ---------------------------------------------------------------------------
# command_hash stability
# ---------------------------------------------------------------------------

def test_command_hash_same_for_same_step():
    cache = StepCache(path=Path("/tmp/unused"))
    s = _step()
    assert cache.command_hash(s) == cache.command_hash(s)


def test_command_hash_differs_on_command_change():
    cache = StepCache(path=Path("/tmp/unused"))
    s1 = _step(command="echo a")
    s2 = _step(command="echo b")
    assert cache.command_hash(s1) != cache.command_hash(s2)


# ---------------------------------------------------------------------------
# is_cached / record
# ---------------------------------------------------------------------------

def test_not_cached_initially():
    cache = StepCache(path=Path("/tmp/unused"))
    assert cache.is_cached(_step()) is False


def test_cached_after_successful_record():
    cache = StepCache(path=Path("/tmp/unused"))
    s = _step()
    cache.record(s, exit_code=0)
    assert cache.is_cached(s) is True


def test_not_cached_after_failed_record():
    cache = StepCache(path=Path("/tmp/unused"))
    s = _step()
    cache.record(s, exit_code=1)
    assert cache.is_cached(s) is False


def test_cache_invalidated_after_command_change():
    cache = StepCache(path=Path("/tmp/unused"))
    s_old = _step(command="echo old")
    cache.record(s_old, exit_code=0)
    s_new = _step(command="echo new")
    assert cache.is_cached(s_new) is False


# ---------------------------------------------------------------------------
# persist / load
# ---------------------------------------------------------------------------

def test_save_and_load(tmp_path):
    p = tmp_path / "cache.json"
    cache = StepCache(path=p)
    s = _step()
    cache.record(s, exit_code=0)
    cache.save()

    loaded = StepCache.load(p)
    assert loaded.is_cached(s) is True


def test_load_missing_file_returns_empty(tmp_path):
    cache = StepCache.load(tmp_path / "no_such_file.json")
    assert cache.is_cached(_step()) is False


def test_load_corrupt_file_returns_empty(tmp_path):
    p = tmp_path / "cache.json"
    p.write_text("not json")
    cache = StepCache.load(p)
    assert cache.is_cached(_step()) is False


# ---------------------------------------------------------------------------
# clear / invalidate
# ---------------------------------------------------------------------------

def test_clear_removes_all_entries():
    cache = StepCache(path=Path("/tmp/unused"))
    s = _step()
    cache.record(s, exit_code=0)
    cache.clear()
    assert cache.is_cached(s) is False


def test_invalidate_removes_single_entry():
    cache = StepCache(path=Path("/tmp/unused"))
    s1 = _step(name="a", command="echo a")
    s2 = _step(name="b", command="echo b")
    cache.record(s1, exit_code=0)
    cache.record(s2, exit_code=0)
    cache.invalidate("a")
    assert cache.is_cached(s1) is False
    assert cache.is_cached(s2) is True


# ---------------------------------------------------------------------------
# maybe_load_cache
# ---------------------------------------------------------------------------

def test_maybe_load_cache_disabled_returns_none(tmp_path):
    assert maybe_load_cache(enabled=False) is None


def test_maybe_load_cache_enabled_returns_instance(tmp_path):
    p = str(tmp_path / "c.json")
    result = maybe_load_cache(enabled=True, path=p)
    assert isinstance(result, StepCache)
