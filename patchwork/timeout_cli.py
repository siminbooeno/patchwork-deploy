"""CLI sub-commands for inspecting timeout information from audit logs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from patchwork.audit import AuditEntry


def _load_entries(audit_file: str) -> list[dict]:
    path = Path(audit_file)
    if not path.exists():
        return []
    entries: list[dict] = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def cmd_timeouts(args: argparse.Namespace) -> int:
    """List runs that contained at least one timed-out step."""
    entries = _load_entries(args.audit_file)
    hits = [
        e for e in entries
        if e.get("extra", {}).get("any_timed_out", False)
    ]
    if not hits:
        print("No timed-out runs found.")
        return 0
    for e in hits:
        timed_out = e.get("extra", {}).get("timed_out_steps", [])
        print(f"[{e.get('timestamp', '?')}] pipeline={e.get('pipeline')} "
              f"timed_out={timed_out}")
    return 0


def cmd_timeout_stats(args: argparse.Namespace) -> int:
    """Print aggregate timeout statistics."""
    entries = _load_entries(args.audit_file)
    total_runs = len(entries)
    timed_out_runs = sum(
        1 for e in entries if e.get("extra", {}).get("any_timed_out", False)
    )
    step_counts: dict[str, int] = {}
    for e in entries:
        for step in e.get("extra", {}).get("timed_out_steps", []):
            step_counts[step] = step_counts.get(step, 0) + 1

    print(f"Total runs       : {total_runs}")
    print(f"Runs with timeout: {timed_out_runs}")
    if step_counts:
        print("Timed-out steps  :")
        for name, count in sorted(step_counts.items(), key=lambda x: -x[1]):
            print(f"  {name}: {count}")
    else:
        print("Timed-out steps  : none")
    return 0


def build_timeout_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--audit-file", default="patchwork-audit.jsonl",
        help="Path to audit JSONL file (default: patchwork-audit.jsonl)",
    )

    p_list = subparsers.add_parser(
        "timeouts", parents=[common],
        help="List runs that had timed-out steps",
    )
    p_list.set_defaults(func=cmd_timeouts)

    p_stats = subparsers.add_parser(
        "timeout-stats", parents=[common],
        help="Show aggregate timeout statistics",
    )
    p_stats.set_defaults(func=cmd_timeout_stats)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="patchwork-timeout",
        description="Inspect step timeout data from audit logs",
    )
    sub = parser.add_subparsers(dest="command")
    build_timeout_parser(sub)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
