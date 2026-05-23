"""Step dependency resolution — ensures steps run only after their dependencies succeed."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


class DependencyError(Exception):
    def __str__(self) -> str:
        return self.args[0]


@dataclass
class DependencyGraph:
    """Adjacency list: step_name -> list of names it depends on."""
    deps: Dict[str, List[str]] = field(default_factory=dict)

    def add(self, step_name: str, depends_on: List[str]) -> None:
        self.deps[step_name] = depends_on

    def all_steps(self) -> Set[str]:
        names: Set[str] = set(self.deps.keys())
        for deps in self.deps.values():
            names.update(deps)
        return names


def parse_depends_on(raw: object) -> List[str]:
    """Accept a string shorthand or a list of step names."""
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    if isinstance(raw, list):
        return [str(s).strip() for s in raw if str(s).strip()]
    raise DependencyError(
        f"depends_on must be a string or list, got {type(raw).__name__!r}"
    )


def build_graph(steps: List[object]) -> DependencyGraph:
    """Build a DependencyGraph from a list of Step-like objects."""
    graph = DependencyGraph()
    for step in steps:
        name: str = getattr(step, "name", "")
        raw = getattr(step, "depends_on", None)
        graph.add(name, parse_depends_on(raw))
    return graph


def topological_sort(graph: DependencyGraph) -> List[str]:
    """Return step names in a valid execution order (Kahn's algorithm).

    Raises DependencyError on cycles or unknown references.
    """
    known = set(graph.deps.keys())
    for step, deps in graph.deps.items():
        for dep in deps:
            if dep not in known:
                raise DependencyError(
                    f"Step {step!r} depends on unknown step {dep!r}"
                )

    in_degree: Dict[str, int] = {s: 0 for s in known}
    for deps in graph.deps.values():
        for dep in deps:
            in_degree[dep] = in_degree.get(dep, 0)  # already counted above
    # recalculate: count how many steps point TO each node
    in_degree = {s: 0 for s in known}
    for deps in graph.deps.values():
        for dep in deps:
            in_degree[dep] += 1

    queue = sorted(s for s, deg in in_degree.items() if deg == 0)
    order: List[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for candidate, deps in graph.deps.items():
            if node in deps:
                in_degree[candidate] -= 1
                if in_degree[candidate] == 0:
                    queue.append(candidate)
                    queue.sort()
    if len(order) != len(known):
        cycle = sorted(known - set(order))
        raise DependencyError(f"Cycle detected among steps: {cycle}")
    return order


def is_runnable(step_name: str, graph: DependencyGraph, succeeded: Set[str]) -> bool:
    """Return True if all dependencies of *step_name* have succeeded."""
    return all(dep in succeeded for dep in graph.deps.get(step_name, []))
