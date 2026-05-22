"""Tests for patchwork.hooks."""

import pytest

from patchwork.config import Step
from patchwork.executor import StepResult
from patchwork.hooks import HookSet, HookResult, parse_hooks, run_hooks


def _ok_result() -> StepResult:
    step = Step(name="deploy", run="echo hi")
    return StepResult(step=step, returncode=0, stdout="hi", skipped=False)


def _fail_result() -> StepResult:
    step = Step(name="deploy", run="exit 1")
    return StepResult(step=step, returncode=1, stdout="", skipped=False)


def test_parse_hooks_empty():
    hs = parse_hooks({})
    assert hs.on_success == []
    assert hs.on_failure == []
    assert hs.on_always == []


def test_parse_hooks_string_shorthand():
    hs = parse_hooks({"on_success": "echo done", "on_always": "echo always"})
    assert hs.on_success == ["echo done"]
    assert hs.on_always == ["echo always"]


def test_parse_hooks_list():
    hs = parse_hooks({"on_failure": ["echo a", "echo b"]})
    assert hs.on_failure == ["echo a", "echo b"]


def test_dry_run_returns_placeholder():
    hs = HookSet(on_success=["echo success"], on_always=["echo always"])
    results = run_hooks(hs, _ok_result(), dry_run=True)
    assert len(results) == 2
    assert all(r.ok for r in results)
    assert all(r.stdout == "[dry-run]" for r in results)


def test_on_success_runs_when_ok():
    hs = HookSet(on_success=["echo yes"], on_failure=["echo no"])
    results = run_hooks(hs, _ok_result(), dry_run=False)
    hook_types = [r.hook_type for r in results]
    assert "on_success" in hook_types
    assert "on_failure" not in hook_types


def test_on_failure_runs_when_failed():
    hs = HookSet(on_success=["echo yes"], on_failure=["echo no"])
    results = run_hooks(hs, _fail_result(), dry_run=False)
    hook_types = [r.hook_type for r in results]
    assert "on_failure" in hook_types
    assert "on_success" not in hook_types


def test_on_always_runs_regardless():
    hs = HookSet(on_always=["echo always"])
    for result in (_ok_result(), _fail_result()):
        results = run_hooks(hs, result, dry_run=False)
        assert any(r.hook_type == "on_always" for r in results)


def test_failed_hook_captured():
    hs = HookSet(on_always=["exit 42"])
    results = run_hooks(hs, _ok_result(), dry_run=False)
    assert results[0].returncode == 42
    assert not results[0].ok
