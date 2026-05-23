"""Tests for patchwork.retry."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from patchwork.executor import StepResult
from patchwork.retry import RetryOutcome, RetryPolicy, parse_retry, run_with_retry


def _ok() -> StepResult:
    return StepResult(name="s", returncode=0, stdout="", stderr="", skipped=False)


def _fail() -> StepResult:
    return StepResult(name="s", returncode=1, stdout="", stderr="err", skipped=False)


# ---------------------------------------------------------------------------
# parse_retry
# ---------------------------------------------------------------------------

def test_parse_retry_none_returns_defaults():
    p = parse_retry(None)
    assert p.max_attempts == 1
    assert p.delay_seconds == 0.0
    assert p.backoff_factor == 1.0


def test_parse_retry_int_shorthand():
    p = parse_retry(3)
    assert p.max_attempts == 3


def test_parse_retry_dict_full():
    p = parse_retry({"attempts": 4, "delay": 2.5, "backoff": 2.0})
    assert p.max_attempts == 4
    assert p.delay_seconds == 2.5
    assert p.backoff_factor == 2.0


def test_parse_retry_dict_partial():
    p = parse_retry({"attempts": 2})
    assert p.max_attempts == 2
    assert p.delay_seconds == 0.0


def test_parse_retry_invalid_raises():
    with pytest.raises(ValueError):
        parse_retry("bad")


# ---------------------------------------------------------------------------
# run_with_retry
# ---------------------------------------------------------------------------

def test_single_attempt_success():
    policy = RetryPolicy(max_attempts=1)
    outcome = run_with_retry(policy, _ok)
    assert outcome.succeeded
    assert outcome.total_attempts == 1


def test_succeeds_on_second_attempt():
    calls = [_fail, _ok]
    idx = iter(calls)
    outcome = run_with_retry(RetryPolicy(max_attempts=3), lambda: next(idx)(), _sleep=lambda _: None)
    assert outcome.succeeded
    assert outcome.total_attempts == 2


def test_exhausts_all_attempts_on_persistent_failure():
    policy = RetryPolicy(max_attempts=3)
    outcome = run_with_retry(policy, _fail, _sleep=lambda _: None)
    assert not outcome.succeeded
    assert outcome.total_attempts == 3


def test_sleep_called_between_attempts():
    sleep_mock = MagicMock()
    policy = RetryPolicy(max_attempts=3, delay_seconds=1.0)
    run_with_retry(policy, _fail, _sleep=sleep_mock)
    assert sleep_mock.call_count == 2


def test_no_sleep_on_dry_run():
    sleep_mock = MagicMock()
    policy = RetryPolicy(max_attempts=3, delay_seconds=1.0)
    run_with_retry(policy, _fail, dry_run=True, _sleep=sleep_mock)
    sleep_mock.assert_not_called()


def test_backoff_increases_delay():
    delays: list = []
    policy = RetryPolicy(max_attempts=3, delay_seconds=1.0, backoff_factor=2.0)
    run_with_retry(policy, _fail, _sleep=delays.append)
    assert delays == [1.0, 2.0]


def test_outcome_contains_last_result():
    """The outcome should expose the result from the final attempt."""
    policy = RetryPolicy(max_attempts=3)
    outcome = run_with_retry(policy, _fail, _sleep=lambda _: None)
    assert outcome.last_result is not None
    assert outcome.last_result.returncode == 1
    assert outcome.last_result.stderr == "err"
