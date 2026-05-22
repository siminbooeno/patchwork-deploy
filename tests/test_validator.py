"""Tests for patchwork.validator."""

from __future__ import annotations

import pytest

from patchwork.config import PipelineConfig, Step
from patchwork.validator import validate, ValidationResult


def _make_config(**kwargs) -> PipelineConfig:
    defaults = dict(
        pipeline_name="deploy",
        steps=[
            Step(name="build", command="make build"),
        ],
        env={},
        notify_on_failure=None,
    )
    defaults.update(kwargs)
    return PipelineConfig(**defaults)


def _step(**kwargs) -> Step:
    defaults = dict(name="step", command="echo hi", rollback=None, timeout=None, env={})
    defaults.update(kwargs)
    return Step(**defaults)


def test_valid_config_passes():
    result = validate(_make_config())
    assert result.ok
    assert str(result) == "Validation passed."


def test_empty_pipeline_name_fails():
    result = validate(_make_config(pipeline_name=""))
    assert not result.ok
    assert any("name" in e.field for e in result.errors)


def test_blank_pipeline_name_fails():
    result = validate(_make_config(pipeline_name="   "))
    assert not result.ok


def test_no_steps_fails():
    result = validate(_make_config(steps=[]))
    assert not result.ok
    assert any("steps" in e.field for e in result.errors)


def test_step_empty_command_fails():
    result = validate(_make_config(steps=[_step(command="")]))
    assert not result.ok
    assert any("command" in e.field for e in result.errors)


def test_duplicate_step_names_fail():
    steps = [_step(name="deploy", command="echo a"), _step(name="deploy", command="echo b")]
    result = validate(_make_config(steps=steps))
    assert not result.ok
    assert any("Duplicate" in e.message for e in result.errors)


def test_negative_timeout_fails():
    result = validate(_make_config(steps=[_step(timeout=-5)]))
    assert not result.ok
    assert any("timeout" in e.field for e in result.errors)


def test_zero_timeout_fails():
    result = validate(_make_config(steps=[_step(timeout=0)]))
    assert not result.ok


def test_positive_timeout_passes():
    result = validate(_make_config(steps=[_step(timeout=30)]))
    assert result.ok


def test_blank_rollback_fails():
    result = validate(_make_config(steps=[_step(rollback="   ")]))
    assert not result.ok
    assert any("rollback" in e.field for e in result.errors)


def test_none_rollback_passes():
    result = validate(_make_config(steps=[_step(rollback=None)]))
    assert result.ok


def test_multiple_errors_reported():
    result = validate(_make_config(pipeline_name="", steps=[]))
    assert len(result.errors) >= 2
    assert "Validation failed:" in str(result)
