"""Audit log: records each pipeline run to a append-only JSONL file."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from patchwork.executor import ExecutionReport


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class AuditEntry:
    timestamp: str
    pipeline: str
    success: bool
    dry_run: bool
    steps_total: int
    steps_ok: int
    failed_step: Optional[str]
    duration_seconds: float
    tags: List[str] = field(default_factory=list)


def build_entry(
    report: ExecutionReport,
    pipeline_name: str,
    dry_run: bool = False,
    tags: Optional[List[str]] = None,
) -> AuditEntry:
    """Build an AuditEntry from an ExecutionReport."""
    steps_ok = sum(1 for r in report.results if r.success)
    failed = report.failed_step
    duration = sum(
        r.duration_seconds for r in report.results if r.duration_seconds is not None
    )
    return AuditEntry(
        timestamp=_iso_now(),
        pipeline=pipeline_name,
        success=report.success,
        dry_run=dry_run,
        steps_total=len(report.results),
        steps_ok=steps_ok,
        failed_step=failed.name if failed else None,
        duration_seconds=round(duration, 4),
        tags=tags or [],
    )


def write_entry(entry: AuditEntry, path: Path) -> None:
    """Append *entry* as a single JSON line to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry)) + "\n")


def maybe_write_entry(
    report: ExecutionReport,
    pipeline_name: str,
    dry_run: bool = False,
    tags: Optional[List[str]] = None,
    audit_file: Optional[str] = None,
) -> Optional[Path]:
    """Write an audit entry if *audit_file* is provided (or PATCHWORK_AUDIT env var)."""
    target = audit_file or os.environ.get("PATCHWORK_AUDIT")
    if not target:
        return None
    path = Path(target)
    entry = build_entry(report, pipeline_name, dry_run=dry_run, tags=tags)
    write_entry(entry, path)
    return path


def read_entries(path: Path) -> List[AuditEntry]:
    """Read all AuditEntry records from a JSONL audit file."""
    if not path.exists():
        return []
    entries = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(AuditEntry(**json.loads(line)))
    return entries
