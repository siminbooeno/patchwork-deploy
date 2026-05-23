"""Tests for patchwork.step_condition."""
import pytest

from patchwork.step_condition import (
    Condition,
    ConditionError,
    evaluate_condition,
    parse_condition,
)


# ---------------------------------------------------------------------------
# parse_condition
# ---------------------------------------------------------------------------

def test_parse_none_returns_empty_condition():
    c = parse_condition(None)
    assert c.is_empty()


def test_parse_on_success():
    c = parse_condition("on_success")
    assert c.on_success is True
    assert c.on_failure is False
    assert c.env_var is None


def test_parse_on_failure():
    c = parse_condition("on_failure")
    assert c.on_failure is True
    assert c.on_success is False


def test_parse_env_var_only():
    c = parse_condition("env:DEPLOY_ENV")
    assert c.env_var == "DEPLOY_ENV"
    assert c.env_equals is None


def test_parse_env_var_with_equals():
    c = parse_condition("env:DEPLOY_ENV=production")
    assert c.env_var == "DEPLOY_ENV"
    assert c.env_equals == "production"


def test_parse_invalid_string_raises():
    with pytest.raises(ConditionError, match="unrecognised condition"):
        parse_condition("unknown_keyword")


def test_parse_non_string_raises():
    with pytest.raises(ConditionError, match="must be a string"):
        parse_condition(42)


# ---------------------------------------------------------------------------
# evaluate_condition
# ---------------------------------------------------------------------------

def test_empty_condition_always_runs():
    assert evaluate_condition(Condition()) is True


def test_on_success_runs_when_previous_succeeded():
    assert evaluate_condition(Condition(on_success=True), previous_succeeded=True) is True


def test_on_success_skips_when_previous_failed():
    assert evaluate_condition(Condition(on_success=True), previous_succeeded=False) is False


def test_on_success_skips_when_no_previous():
    assert evaluate_condition(Condition(on_success=True), previous_succeeded=None) is False


def test_on_failure_runs_when_previous_failed():
    assert evaluate_condition(Condition(on_failure=True), previous_succeeded=False) is True


def test_on_failure_skips_when_previous_succeeded():
    assert evaluate_condition(Condition(on_failure=True), previous_succeeded=True) is False


def test_env_var_present_runs():
    env = {"DEPLOY_ENV": "staging"}
    c = Condition(env_var="DEPLOY_ENV")
    assert evaluate_condition(c, environ=env) is True


def test_env_var_absent_skips():
    c = Condition(env_var="MISSING_VAR")
    assert evaluate_condition(c, environ={}) is False


def test_env_var_equals_match_runs():
    env = {"DEPLOY_ENV": "production"}
    c = Condition(env_var="DEPLOY_ENV", env_equals="production")
    assert evaluate_condition(c, environ=env) is True


def test_env_var_equals_mismatch_skips():
    env = {"DEPLOY_ENV": "staging"}
    c = Condition(env_var="DEPLOY_ENV", env_equals="production")
    assert evaluate_condition(c, environ=env) is False
