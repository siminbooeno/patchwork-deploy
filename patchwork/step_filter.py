"""Step filtering: run only a subset of pipeline steps by tag or name."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from patchwork.config import Step


@dataclass
class FilterCriteria:
    """Criteria used to select which steps to run."""
    tags: List[str] = field(default_factory=list)
    names: List[str] = field(default_factory=list)
    skip_tags: List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.tags and not self.names and not self.skip_tags


def _step_matches_include(step: Step, criteria: FilterCriteria) -> bool:
    """Return True if the step satisfies any positive filter."""
    if criteria.names and step.name in criteria.names:
        return True
    if criteria.tags:
        step_tags = set(step.tags or [])
        if step_tags.intersection(criteria.tags):
            return True
    # No positive filter defined — include by default
    if not criteria.names and not criteria.tags:
        return True
    return False


def _step_is_skipped(step: Step, criteria: FilterCriteria) -> bool:
    """Return True if the step should be excluded via skip_tags."""
    if not criteria.skip_tags:
        return False
    step_tags = set(step.tags or [])
    return bool(step_tags.intersection(criteria.skip_tags))


def apply_filter(steps: Sequence[Step], criteria: FilterCriteria) -> List[Step]:
    """Return the subset of *steps* that match *criteria*."""
    if criteria.is_empty:
        return list(steps)
    return [
        s for s in steps
        if _step_matches_include(s, criteria) and not _step_is_skipped(s, criteria)
    ]


def parse_filter_criteria(
    tags: Optional[Sequence[str]] = None,
    names: Optional[Sequence[str]] = None,
    skip_tags: Optional[Sequence[str]] = None,
) -> FilterCriteria:
    """Build a :class:`FilterCriteria` from raw CLI / API inputs."""
    return FilterCriteria(
        tags=list(tags or []),
        names=list(names or []),
        skip_tags=list(skip_tags or []),
    )
