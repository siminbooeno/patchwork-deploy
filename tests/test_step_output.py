"""Tests for patchwork.step_output."""
import pytest

from patchwork.step_output import (
    StepOutput,
    capture_output,
    format_output,
)


def test_empty_output_has_no_output():
    out = capture_output("deploy", "", "")
    assert not out.has_output()
    assert out.stdout == ""
    assert out.stderr == ""
    assert not out.truncated


def test_stdout_split_into_lines():
    out = capture_output("build", "line1\nline2\nline3", "")
    assert out.stdout_lines == ["line1", "line2", "line3"]
    assert out.has_output()


def test_stderr_split_into_lines():
    out = capture_output("build", "", "err1\nerr2")
    assert out.stderr_lines == ["err1", "err2"]


def test_no_truncation_under_limit():
    stdout = "\n".join(f"line{i}" for i in range(10))
    out = capture_output("step", stdout, "", max_lines=20)
    assert not out.truncated
    assert len(out.stdout_lines) == 10


def test_truncation_stdout_only():
    stdout = "\n".join(f"line{i}" for i in range(50))
    out = capture_output("step", stdout, "", max_lines=20)
    assert out.truncated
    assert len(out.stdout_lines) == 20


def test_truncation_stderr_only():
    stderr = "\n".join(f"err{i}" for i in range(50))
    out = capture_output("step", "", stderr, max_lines=10)
    assert out.truncated
    assert len(out.stderr_lines) == 10


def test_truncation_splits_budget_between_streams():
    stdout = "\n".join(f"o{i}" for i in range(30))
    stderr = "\n".join(f"e{i}" for i in range(30))
    out = capture_output("step", stdout, stderr, max_lines=20)
    assert out.truncated
    assert len(out.stdout_lines) + len(out.stderr_lines) == 20


def test_as_dict_keys():
    out = capture_output("deploy", "ok", "")
    d = out.as_dict()
    assert set(d.keys()) == {"step", "stdout", "stderr", "truncated"}
    assert d["step"] == "deploy"
    assert d["truncated"] is False


def test_format_output_contains_stdout_label():
    out = capture_output("run", "hello\nworld", "")
    text = format_output(out)
    assert "[stdout]" in text
    assert "hello" in text
    assert "world" in text


def test_format_output_contains_stderr_label():
    out = capture_output("run", "", "oops")
    text = format_output(out)
    assert "[stderr]" in text
    assert "oops" in text


def test_format_output_truncation_note():
    stdout = "\n".join(f"l{i}" for i in range(50))
    out = capture_output("run", stdout, "", max_lines=5)
    text = format_output(out)
    assert "truncated" in text


def test_format_output_empty_is_empty_string():
    out = capture_output("run", "", "")
    assert format_output(out) == ""
