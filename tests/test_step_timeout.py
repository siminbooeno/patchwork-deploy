"""Tests for patchwork.step_timeout."""
import pytest

from patchwork.step_timeout import (
    TimeoutPolicy,
    TimeoutReport,
    apply_timeout,
    parse_timeout,
    _parse_duration,
)


# ---------------------------------------------------------------------------
# parse_timeout
# ---------------------------------------------------------------------------

def test_parse_none_returns_no_limit():
    p = parse_timeout(None)
    assert p.seconds is None
    assert not p.enabled


def test_parse_int_returns_seconds():
    p = parse_timeout(10)
    assert p.seconds == 10.0
    assert p.enabled


def test_parse_float_returns_seconds():
    p = parse_timeout(1.5)
    assert p.seconds == 1.5


def test_parse_string_seconds():
    assert parse_timeout("30s").seconds == 30.0


def test_parse_string_minutes():
    assert parse_timeout("2m").seconds == 120.0


def test_parse_string_hours():
    assert parse_timeout("1h").seconds == 3600.0


def test_parse_bare_number_string():
    assert parse_timeout("45").seconds == 45.0


def test_parse_invalid_string_raises():
    with pytest.raises(ValueError, match="invalid timeout"):
        parse_timeout("abc")


def test_parse_zero_raises():
    with pytest.raises(ValueError, match="positive"):
        parse_timeout(0)


def test_parse_negative_raises():
    with pytest.raises(ValueError, match="positive"):
        parse_timeout(-5)


def test_parse_wrong_type_raises():
    with pytest.raises(TypeError):
        parse_timeout([10])


# ---------------------------------------------------------------------------
# _parse_duration edge cases
# ---------------------------------------------------------------------------

def test_parse_duration_fractional_minutes():
    assert _parse_duration("1.5m") == 90.0


def test_parse_duration_zero_string_raises():
    with pytest.raises(ValueError):
        _parse_duration("0s")


# ---------------------------------------------------------------------------
# TimeoutReport
# ---------------------------------------------------------------------------

def test_report_initially_empty():
    r = TimeoutReport()
    assert not r.any_timed_out
    assert r.timed_out_steps == []


def test_report_records_step():
    r = TimeoutReport()
    r.record_timeout("deploy")
    assert r.any_timed_out
    assert "deploy" in r.timed_out_steps


def test_report_as_dict():
    r = TimeoutReport()
    r.record_timeout("build")
    d = r.as_dict()
    assert d["any_timed_out"] is True
    assert d["timed_out_steps"] == ["build"]


# ---------------------------------------------------------------------------
# apply_timeout (integration with real subprocesses)
# ---------------------------------------------------------------------------

import subprocess


def _popen(cmd: str) -> "subprocess.Popen[str]":
    return subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True
    )


def test_apply_timeout_fast_command_succeeds():
    report = TimeoutReport()
    proc = _popen("echo hello")
    stdout, rc = apply_timeout(proc, TimeoutPolicy(seconds=5.0), "echo", report)
    assert rc == 0
    assert "hello" in stdout
    assert not report.any_timed_out


def test_apply_timeout_slow_command_is_killed():
    report = TimeoutReport()
    proc = _popen("sleep 60")
    stdout, rc = apply_timeout(proc, TimeoutPolicy(seconds=0.1), "slow", report)
    assert rc == -1
    assert "timeout" in stdout
    assert report.any_timed_out
    assert "slow" in report.timed_out_steps


def test_apply_timeout_no_limit_does_not_kill():
    report = TimeoutReport()
    proc = _popen("echo done")
    stdout, rc = apply_timeout(proc, TimeoutPolicy(seconds=None), "nolimit", report)
    assert rc == 0
    assert not report.any_timed_out
