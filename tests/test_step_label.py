"""Tests for patchwork.step_label."""
import pytest
from patchwork.step_label import StepLabel, parse_label, group_labels


# ---------------------------------------------------------------------------
# parse_label
# ---------------------------------------------------------------------------

def test_parse_none_returns_fallback():
    lbl = parse_label(None, "my-step")
    assert lbl.display == "my-step"
    assert lbl.group is None
    assert lbl.icon is None
    assert lbl.tags == []


def test_parse_string_sets_display():
    lbl = parse_label("Deploy app", "fallback")
    assert lbl.display == "Deploy app"
    assert lbl.group is None


def test_parse_blank_string_uses_fallback():
    lbl = parse_label("   ", "fallback-name")
    assert lbl.display == "fallback-name"


def test_parse_dict_full():
    raw = {
        "display": "Build Image",
        "group": "ci",
        "icon": "🔨",
        "tags": ["docker", "build"],
    }
    lbl = parse_label(raw, "fallback")
    assert lbl.display == "Build Image"
    assert lbl.group == "ci"
    assert lbl.icon == "🔨"
    assert lbl.tags == ["docker", "build"]


def test_parse_dict_missing_display_uses_fallback():
    lbl = parse_label({"group": "ops"}, "step-x")
    assert lbl.display == "step-x"
    assert lbl.group == "ops"


def test_parse_dict_tags_as_csv_string():
    lbl = parse_label({"display": "Run tests", "tags": "unit, integration"}, "t")
    assert lbl.tags == ["unit", "integration"]


def test_parse_unknown_type_returns_fallback():
    lbl = parse_label(42, "step-q")
    assert lbl.display == "step-q"


# ---------------------------------------------------------------------------
# StepLabel.short / full
# ---------------------------------------------------------------------------

def test_short_no_icon():
    lbl = StepLabel(display="Deploy")
    assert lbl.short() == "Deploy"


def test_short_with_icon():
    lbl = StepLabel(display="Deploy", icon="🚀")
    assert lbl.short() == "🚀  Deploy"


def test_full_no_group():
    lbl = StepLabel(display="Deploy")
    assert lbl.full() == "Deploy"


def test_full_with_group():
    lbl = StepLabel(display="Deploy", group="production")
    assert lbl.full() == "[production] Deploy"


def test_full_with_group_and_icon():
    lbl = StepLabel(display="Deploy", group="prod", icon="🚀")
    assert lbl.full() == "[prod] 🚀  Deploy"


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_round_trip():
    lbl = StepLabel(display="X", group="g", icon="★", tags=["a"])
    d = lbl.as_dict()
    assert d == {"display": "X", "group": "g", "icon": "★", "tags": ["a"]}


# ---------------------------------------------------------------------------
# group_labels
# ---------------------------------------------------------------------------

def test_group_labels_single_group():
    labels = {
        "step-a": parse_label({"display": "A", "group": "ci"}, "step-a"),
        "step-b": parse_label({"display": "B", "group": "ci"}, "step-b"),
    }
    groups = group_labels(labels)
    assert set(groups["ci"]) == {"step-a", "step-b"}


def test_group_labels_ungrouped():
    labels = {"step-x": parse_label(None, "step-x")}
    groups = group_labels(labels)
    assert "step-x" in groups["(ungrouped)"]


def test_group_labels_mixed():
    labels = {
        "a": parse_label({"display": "A", "group": "ci"}, "a"),
        "b": parse_label(None, "b"),
    }
    groups = group_labels(labels)
    assert "a" in groups["ci"]
    assert "b" in groups["(ungrouped)"]
