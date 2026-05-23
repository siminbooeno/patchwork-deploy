"""Tests for patchwork.step_dependency."""
import pytest
from patchwork.step_dependency import (
    DependencyError,
    DependencyGraph,
    build_graph,
    is_runnable,
    parse_depends_on,
    topological_sort,
)


# ---------------------------------------------------------------------------
# parse_depends_on
# ---------------------------------------------------------------------------

def test_parse_none_returns_empty():
    assert parse_depends_on(None) == []


def test_parse_string_single():
    assert parse_depends_on("build") == ["build"]


def test_parse_string_blank_returns_empty():
    assert parse_depends_on("   ") == []


def test_parse_list():
    assert parse_depends_on(["build", "test"]) == ["build", "test"]


def test_parse_list_filters_blank():
    assert parse_depends_on(["build", "", "  "]) == ["build"]


def test_parse_invalid_type_raises():
    with pytest.raises(DependencyError, match="list"):
        parse_depends_on(123)


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------

class _FakeStep:
    def __init__(self, name, depends_on=None):
        self.name = name
        self.depends_on = depends_on


def test_build_graph_no_deps():
    steps = [_FakeStep("a"), _FakeStep("b")]
    g = build_graph(steps)
    assert g.deps == {"a": [], "b": []}


def test_build_graph_with_deps():
    steps = [_FakeStep("a"), _FakeStep("b", depends_on="a")]
    g = build_graph(steps)
    assert g.deps["b"] == ["a"]


# ---------------------------------------------------------------------------
# topological_sort
# ---------------------------------------------------------------------------

def test_sort_no_deps_returns_all():
    g = DependencyGraph(deps={"a": [], "b": [], "c": []})
    order = topological_sort(g)
    assert set(order) == {"a", "b", "c"}


def test_sort_linear_chain():
    g = DependencyGraph(deps={"a": [], "b": ["a"], "c": ["b"]})
    order = topological_sort(g)
    assert order.index("a") < order.index("b")
    assert order.index("b") < order.index("c")


def test_sort_unknown_dep_raises():
    g = DependencyGraph(deps={"a": ["missing"]})
    with pytest.raises(DependencyError, match="unknown step"):
        topological_sort(g)


def test_sort_cycle_raises():
    g = DependencyGraph(deps={"a": ["b"], "b": ["a"]})
    with pytest.raises(DependencyError, match="Cycle"):
        topological_sort(g)


# ---------------------------------------------------------------------------
# is_runnable
# ---------------------------------------------------------------------------

def test_is_runnable_no_deps():
    g = DependencyGraph(deps={"a": []})
    assert is_runnable("a", g, succeeded=set()) is True


def test_is_runnable_dep_succeeded():
    g = DependencyGraph(deps={"b": ["a"]})
    assert is_runnable("b", g, succeeded={"a"}) is True


def test_is_runnable_dep_not_succeeded():
    g = DependencyGraph(deps={"b": ["a"]})
    assert is_runnable("b", g, succeeded=set()) is False


def test_is_runnable_multiple_deps_partial():
    g = DependencyGraph(deps={"c": ["a", "b"]})
    assert is_runnable("c", g, succeeded={"a"}) is False
    assert is_runnable("c", g, succeeded={"a", "b"}) is True
