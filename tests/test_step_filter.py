"""Tests for patchwork.step_filter."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import pytest

from patchwork.step_filter import (
    FilterCriteria,
    apply_filter,
    parse_filter_criteria,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _step(name: str, tags: Optional[List[str]] = None):
    """Create a minimal Step-like object without importing config."""
    from patchwork.config import Step
    return Step(name=name, command=f"echo {name}", tags=tags or [])


# ---------------------------------------------------------------------------
# parse_filter_criteria
# ---------------------------------------------------------------------------

def test_parse_empty_criteria_is_empty():
    fc = parse_filter_criteria()
    assert fc.is_empty


def test_parse_with_tags_not_empty():
    fc = parse_filter_criteria(tags=["deploy"])
    assert not fc.is_empty
    assert fc.tags == ["deploy"]


def test_parse_with_names():
    fc = parse_filter_criteria(names=["build", "test"])
    assert fc.names == ["build", "test"]


# ---------------------------------------------------------------------------
# apply_filter — empty criteria
# ---------------------------------------------------------------------------

def test_empty_criteria_returns_all_steps():
    steps = [_step("a"), _step("b"), _step("c")]
    result = apply_filter(steps, FilterCriteria())
    assert [s.name for s in result] == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# apply_filter — tag filtering
# ---------------------------------------------------------------------------

def test_filter_by_tag_includes_matching():
    steps = [
        _step("build", tags=["ci"]),
        _step("deploy", tags=["deploy"]),
        _step("notify", tags=["ci"]),
    ]
    fc = parse_filter_criteria(tags=["ci"])
    result = apply_filter(steps, fc)
    assert [s.name for s in result] == ["build", "notify"]


def test_filter_by_tag_no_match_returns_empty():
    steps = [_step("build", tags=["ci"]), _step("deploy", tags=["deploy"])]
    fc = parse_filter_criteria(tags=["staging"])
    assert apply_filter(steps, fc) == []


# ---------------------------------------------------------------------------
# apply_filter — name filtering
# ---------------------------------------------------------------------------

def test_filter_by_name():
    steps = [_step("build"), _step("test"), _step("deploy")]
    fc = parse_filter_criteria(names=["test", "deploy"])
    result = apply_filter(steps, fc)
    assert [s.name for s in result] == ["test", "deploy"]


# ---------------------------------------------------------------------------
# apply_filter — skip_tags
# ---------------------------------------------------------------------------

def test_skip_tags_excludes_matching():
    steps = [
        _step("build", tags=["ci"]),
        _step("notify", tags=["notification"]),
        _step("deploy", tags=["deploy"]),
    ]
    fc = parse_filter_criteria(skip_tags=["notification"])
    result = apply_filter(steps, fc)
    assert [s.name for s in result] == ["build", "deploy"]


def test_skip_tags_combined_with_tags():
    steps = [
        _step("build", tags=["ci"]),
        _step("lint", tags=["ci", "slow"]),
        _step("deploy", tags=["deploy"]),
    ]
    fc = parse_filter_criteria(tags=["ci"], skip_tags=["slow"])
    result = apply_filter(steps, fc)
    assert [s.name for s in result] == ["build"]
