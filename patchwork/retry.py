"""Step retry logic with configurable attempts and delay."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from patchwork.executor import StepResult


@dataclass
class RetryPolicy:
    max_attempts: int = 1
    delay_seconds: float = 0.0
    backoff_factor: float = 1.0


@dataclass
class RetryRecord:
    attempt: int
    result: StepResult


@dataclass
class RetryOutcome:
    final: StepResult
    attempts: List[RetryRecord] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return self.final.returncode == 0

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)


def parse_retry(raw: object) -> RetryPolicy:
    """Parse a retry block from YAML config into a RetryPolicy."""
    if raw is None:
        return RetryPolicy()
    if isinstance(raw, int):
        return RetryPolicy(max_attempts=raw)
    if isinstance(raw, dict):
        return RetryPolicy(
            max_attempts=int(raw.get("attempts", 1)),
            delay_seconds=float(raw.get("delay", 0.0)),
            backoff_factor=float(raw.get("backoff", 1.0)),
        )
    raise ValueError(f"Invalid retry config: {raw!r}")


def run_with_retry(
    policy: RetryPolicy,
    run_fn: Callable[[], StepResult],
    dry_run: bool = False,
    _sleep: Optional[Callable[[float], None]] = None,
) -> RetryOutcome:
    """Execute run_fn up to policy.max_attempts times.

    Args:
        policy:   RetryPolicy controlling attempt count and delays.
        run_fn:   Zero-argument callable that returns a StepResult.
        dry_run:  When True, run_fn is still called (dry-run logic lives
                  inside the executor) but no inter-attempt sleeps occur.
        _sleep:   Injection point for tests; defaults to time.sleep.
    """
    sleep_fn = _sleep if _sleep is not None else time.sleep
    records: List[RetryRecord] = []
    delay = policy.delay_seconds

    for attempt in range(1, policy.max_attempts + 1):
        result = run_fn()
        records.append(RetryRecord(attempt=attempt, result=result))
        if result.returncode == 0:
            break
        if attempt < policy.max_attempts and not dry_run and delay > 0:
            sleep_fn(delay)
            delay *= policy.backoff_factor

    return RetryOutcome(final=records[-1].result, attempts=records)
