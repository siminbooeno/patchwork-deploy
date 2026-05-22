"""Pipeline config validation — checks steps, commands, and rollback sanity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from patchwork.config import PipelineConfig


@dataclass
class ValidationError:
    field: str
    message: str

    def __str__(self) -> str:
        return f"[{self.field}] {self.message}"


@dataclass
class ValidationResult:
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def add(self, field: str, message: str) -> None:
        self.errors.append(ValidationError(field=field, message=message))

    def __str__(self) -> str:
        if self.ok:
            return "Validation passed."
        lines = ["Validation failed:"]
        for e in self.errors:
            lines.append(f"  - {e}")
        return "\n".join(lines)


def validate(config: PipelineConfig) -> ValidationResult:
    """Run all validation checks on a parsed PipelineConfig."""
    result = ValidationResult()

    if not config.pipeline_name or not config.pipeline_name.strip():
        result.add("pipeline.name", "Pipeline name must not be empty.")

    if not config.steps:
        result.add("pipeline.steps", "Pipeline must define at least one step.")

    seen_names: set[str] = set()
    for i, step in enumerate(config.steps):
        prefix = f"steps[{i}] ({step.name!r})"

        if not step.name or not step.name.strip():
            result.add(f"steps[{i}].name", "Step name must not be empty.")

        if step.name in seen_names:
            result.add(prefix, f"Duplicate step name: {step.name!r}.")
        else:
            seen_names.add(step.name)

        if not step.command or not step.command.strip():
            result.add(f"{prefix}.command", "Step command must not be empty.")

        if step.timeout is not None and step.timeout <= 0:
            result.add(f"{prefix}.timeout", "Timeout must be a positive number.")

        if step.rollback and not step.rollback.strip():
            result.add(f"{prefix}.rollback", "Rollback command must not be empty if specified.")

    return result
