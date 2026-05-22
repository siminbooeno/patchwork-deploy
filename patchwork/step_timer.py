"""Step execution timing utilities for patchwork-deploy."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StepTiming:
    """Timing record for a single step."""

    name: str
    duration_seconds: float
    started_at: float  # epoch seconds

    @property
    def duration_ms(self) -> float:
        return self.duration_seconds * 1000

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "started_at": self.started_at,
            "duration_seconds": round(self.duration_seconds, 4),
            "duration_ms": round(self.duration_ms, 2),
        }


@dataclass
class TimingReport:
    """Aggregated timing data for a full pipeline run."""

    timings: List[StepTiming] = field(default_factory=list)

    def record(self, name: str, duration_seconds: float, started_at: float) -> None:
        self.timings.append(StepTiming(name=name, duration_seconds=duration_seconds, started_at=started_at))

    @property
    def total_seconds(self) -> float:
        return sum(t.duration_seconds for t in self.timings)

    @property
    def slowest(self) -> Optional[StepTiming]:
        if not self.timings:
            return None
        return max(self.timings, key=lambda t: t.duration_seconds)

    @property
    def fastest(self) -> Optional[StepTiming]:
        if not self.timings:
            return None
        return min(self.timings, key=lambda t: t.duration_seconds)

    def as_dict(self) -> dict:
        return {
            "total_seconds": round(self.total_seconds, 4),
            "step_count": len(self.timings),
            "slowest": self.slowest.name if self.slowest else None,
            "fastest": self.fastest.name if self.fastest else None,
            "steps": [t.as_dict() for t in self.timings],
        }


class StepTimer:
    """Context manager that measures elapsed time for a step."""

    def __init__(self, name: str, report: TimingReport) -> None:
        self._name = name
        self._report = report
        self._start: float = 0.0

    def __enter__(self) -> "StepTimer":
        self._start = time.monotonic()
        return self

    def __exit__(self, *_) -> None:
        elapsed = time.monotonic() - self._start
        self._report.record(
            name=self._name,
            duration_seconds=elapsed,
            started_at=time.time() - elapsed,
        )
