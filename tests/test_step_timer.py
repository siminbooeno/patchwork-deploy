"""Tests for patchwork.step_timer."""

import time

import pytest

from patchwork.step_timer import StepTiming, StepTimer, TimingReport


# ---------------------------------------------------------------------------
# StepTiming
# ---------------------------------------------------------------------------

def test_step_timing_duration_ms():
    t = StepTiming(name="deploy", duration_seconds=1.5, started_at=0.0)
    assert t.duration_ms == pytest.approx(1500.0)


def test_step_timing_as_dict_keys():
    t = StepTiming(name="build", duration_seconds=0.25, started_at=1_000_000.0)
    d = t.as_dict()
    assert set(d.keys()) == {"name", "started_at", "duration_seconds", "duration_ms"}
    assert d["name"] == "build"


# ---------------------------------------------------------------------------
# TimingReport
# ---------------------------------------------------------------------------

def _make_report(*names_and_durations) -> TimingReport:
    report = TimingReport()
    for name, dur in names_and_durations:
        report.record(name=name, duration_seconds=dur, started_at=0.0)
    return report


def test_empty_report_total_is_zero():
    report = TimingReport()
    assert report.total_seconds == 0.0


def test_empty_report_slowest_fastest_none():
    report = TimingReport()
    assert report.slowest is None
    assert report.fastest is None


def test_total_seconds_sums_all_steps():
    report = _make_report(("a", 1.0), ("b", 2.0), ("c", 0.5))
    assert report.total_seconds == pytest.approx(3.5)


def test_slowest_returns_max_duration_step():
    report = _make_report(("fast", 0.1), ("slow", 5.0), ("medium", 1.0))
    assert report.slowest.name == "slow"


def test_fastest_returns_min_duration_step():
    report = _make_report(("fast", 0.1), ("slow", 5.0), ("medium", 1.0))
    assert report.fastest.name == "fast"


def test_as_dict_structure():
    report = _make_report(("step1", 1.0), ("step2", 2.0))
    d = report.as_dict()
    assert d["step_count"] == 2
    assert d["slowest"] == "step2"
    assert d["fastest"] == "step1"
    assert len(d["steps"]) == 2


# ---------------------------------------------------------------------------
# StepTimer context manager
# ---------------------------------------------------------------------------

def test_step_timer_records_entry():
    report = TimingReport()
    with StepTimer(name="my-step", report=report):
        time.sleep(0.01)

    assert len(report.timings) == 1
    assert report.timings[0].name == "my-step"
    assert report.timings[0].duration_seconds >= 0.01


def test_step_timer_records_multiple_steps():
    report = TimingReport()
    for name in ("step-a", "step-b", "step-c"):
        with StepTimer(name=name, report=report):
            pass

    assert len(report.timings) == 3
    assert [t.name for t in report.timings] == ["step-a", "step-b", "step-c"]


def test_step_timer_exits_on_exception():
    report = TimingReport()
    with pytest.raises(ValueError):
        with StepTimer(name="boom", report=report):
            raise ValueError("oops")

    # timing should still be recorded even when an exception occurs
    assert len(report.timings) == 1
    assert report.timings[0].name == "boom"
