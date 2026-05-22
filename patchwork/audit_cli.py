"""CLI sub-commands for inspecting the audit log."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from patchwork.audit import AuditEntry, read_entries


def _fmt_entry(entry: AuditEntry) -> str:
    status = "OK " if entry.success else "FAIL"
    dry = " [dry-run]" if entry.dry_run else ""
    failed = f"  failed_step={entry.failed_step}" if entry.failed_step else ""
    tags = f"  tags={entry.tags}" if entry.tags else ""
    return (
        f"[{entry.timestamp}] {status}{dry}  pipeline={entry.pipeline}"
        f"  steps={entry.steps_ok}/{entry.steps_total}"
        f"  duration={entry.duration_seconds}s{failed}{tags}"
    )


def cmd_list(args: argparse.Namespace) -> int:
    """Print all audit entries from the log file."""
    path = Path(args.file)
    entries = read_entries(path)
    if not entries:
        print("No audit entries found.")
        return 0
    for entry in entries:
        print(_fmt_entry(entry))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Print summary statistics for the audit log."""
    path = Path(args.file)
    entries = read_entries(path)
    if not entries:
        print("No audit entries found.")
        return 0
    total = len(entries)
    passed = sum(1 for e in entries if e.success)
    failed = total - passed
    avg_dur = sum(e.duration_seconds for e in entries) / total
    print(f"Total runs : {total}")
    print(f"Passed     : {passed}")
    print(f"Failed     : {failed}")
    print(f"Avg duration: {avg_dur:.3f}s")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export audit log as pretty-printed JSON array."""
    from dataclasses import asdict

    path = Path(args.file)
    entries = read_entries(path)
    print(json.dumps([asdict(e) for e in entries], indent=2))
    return 0


def build_audit_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    audit_p = subparsers.add_parser("audit", help="Inspect the audit log")
    audit_sub = audit_p.add_subparsers(dest="audit_cmd", required=True)

    for name, fn, help_text in [
        ("list", cmd_list, "Print all audit entries"),
        ("stats", cmd_stats, "Show summary statistics"),
        ("export", cmd_export, "Export entries as JSON"),
    ]:
        p = audit_sub.add_parser(name, help=help_text)
        p.add_argument("file", help="Path to the JSONL audit file")
        p.set_defaults(func=fn)


def run_audit_command(args: argparse.Namespace) -> int:
    return args.func(args)
