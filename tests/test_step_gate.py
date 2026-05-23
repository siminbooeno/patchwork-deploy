"""Tests for patchwork.step_gate."""
import pytest

from patchwork.step_gate import (
    GatePolicy,
    is_gated,
    parse_gate,
    prompt_gate,
)


# ---------------------------------------------------------------------------
# parse_gate
# ---------------------------------------------------------------------------

def test_parse_none_returns_disabled():
    p = parse_gate(None)
    assert p.enabled is False


def test_parse_false_returns_disabled():
    p = parse_gate(False)
    assert p.enabled is False


def test_parse_true_returns_enabled_default_message():
    p = parse_gate(True)
    assert p.enabled is True
    assert p.message == "Continue?"
    assert p.timeout_seconds is None


def test_parse_string_sets_message():
    p = parse_gate("Deploy to production?")
    assert p.enabled is True
    assert p.message == "Deploy to production?"


def test_parse_dict_full():
    p = parse_gate({"enabled": True, "message": "Sure?", "timeout": 30})
    assert p.enabled is True
    assert p.message == "Sure?"
    assert p.timeout_seconds == 30.0


def test_parse_dict_enabled_false():
    p = parse_gate({"enabled": False, "message": "Ignored"})
    assert p.enabled is False


def test_parse_dict_no_timeout():
    p = parse_gate({"message": "Go?"})
    assert p.timeout_seconds is None


def test_parse_invalid_raises():
    with pytest.raises(ValueError):
        parse_gate(123)


# ---------------------------------------------------------------------------
# is_gated
# ---------------------------------------------------------------------------

def test_is_gated_true():
    assert is_gated(GatePolicy(enabled=True)) is True


def test_is_gated_false():
    assert is_gated(GatePolicy(enabled=False)) is False


# ---------------------------------------------------------------------------
# prompt_gate
# ---------------------------------------------------------------------------

def test_prompt_gate_disabled_returns_true():
    policy = GatePolicy(enabled=False)
    assert prompt_gate(policy, _input=lambda _: "n") is True


def test_prompt_gate_yes_confirmed():
    policy = GatePolicy(enabled=True)
    assert prompt_gate(policy, _input=lambda _: "y") is True


def test_prompt_gate_yes_long_confirmed():
    policy = GatePolicy(enabled=True)
    assert prompt_gate(policy, _input=lambda _: "yes") is True


def test_prompt_gate_no_denied():
    policy = GatePolicy(enabled=True)
    assert prompt_gate(policy, _input=lambda _: "n") is False


def test_prompt_gate_empty_denied():
    policy = GatePolicy(enabled=True)
    assert prompt_gate(policy, _input=lambda _: "") is False


def test_prompt_gate_eof_denied():
    policy = GatePolicy(enabled=True)
    def _raise(_):
        raise EOFError
    assert prompt_gate(policy, _input=_raise) is False


def test_prompt_gate_keyboard_interrupt_denied():
    policy = GatePolicy(enabled=True)
    def _raise(_):
        raise KeyboardInterrupt
    assert prompt_gate(policy, _input=_raise) is False
