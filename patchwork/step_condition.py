"""Conditional step execution based on environment variables or previous step outcomes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import os


class ConditionError(Exception):
    pass


@dataclass
class Condition:
    """Parsed condition attached to a pipeline step."""
    env_var: Optional[str] = None          # e.g. "DEPLOY_ENV"
    env_equals: Optional[str] = None       # e.g. "production"
    on_success: bool = False               # skip if previous step failed
    on_failure: bool = False               # only run if previous step failed

    def is_empty(self) -> bool:
        return (
            self.env_var is None
            and not self.on_success
            and not self.on_failure
        )


def parse_condition(raw) -> Condition:
    """Parse a condition from YAML value.

    Supported shorthands:
      condition: "env:MY_VAR"               -> run only when MY_VAR is set
      condition: "env:MY_VAR=production"    -> run only when MY_VAR==production
      condition: "on_success"               -> run only after a successful step
      condition: "on_failure"               -> run only after a failed step
      condition:                            -> no condition (always run)
    """
    if raw is None:
        return Condition()

    if not isinstance(raw, str):
        raise ConditionError(f"condition must be a string, got {type(raw).__name__!r}")

    value = raw.strip()

    if value == "on_success":
        return Condition(on_success=True)

    if value == "on_failure":
        return Condition(on_failure=True)

    if value.startswith("env:"):
        rest = value[4:]
        if "=" in rest:
            var, eq_val = rest.split("=", 1)
            return Condition(env_var=var.strip(), env_equals=eq_val.strip())
        return Condition(env_var=rest.strip())

    raise ConditionError(
        f"unrecognised condition {value!r}; "
        "expected 'on_success', 'on_failure', or 'env:VAR[=value]'"
    )


def evaluate_condition(
    condition: Condition,
    previous_succeeded: Optional[bool] = None,
    environ: Optional[dict] = None,
) -> bool:
    """Return True if the step should run, False if it should be skipped."""
    if condition.is_empty():
        return True

    env = environ if environ is not None else os.environ

    if condition.on_success:
        return previous_succeeded is True

    if condition.on_failure:
        return previous_succeeded is False

    if condition.env_var is not None:
        actual = env.get(condition.env_var)
        if actual is None:
            return False
        if condition.env_equals is not None:
            return actual == condition.env_equals
        return True

    return True
