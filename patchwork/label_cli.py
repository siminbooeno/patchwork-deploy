"""CLI sub-command: patchwork labels — inspect step labels and groups."""
from __future__ import annotations

import argparse
import sys
from typing import List

from patchwork.config import load_config
from patchwork.step_label import parse_label, group_labels


def _collect_labels(config_path: str):
    """Load config and return (name -> StepLabel) mapping."""
    cfg = load_config(config_path)
    labels = {}
    for step in cfg.steps:
        raw = step.extra.get("label") if hasattr(step, "extra") else None
        labels[step.name] = parse_label(raw, step.name)
    return labels


def cmd_list_labels(args: argparse.Namespace) -> int:
    """List all step labels, optionally filtered by group."""
    try:
        labels = _collect_labels(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for name, lbl in labels.items():
        if args.group and lbl.group != args.group:
            continue
        print(f"  {name:<24} {lbl.full()}")
    return 0


def cmd_list_groups(args: argparse.Namespace) -> int:
    """List steps organised by group."""
    try:
        labels = _collect_labels(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    groups = group_labels(labels)
    for group_name, step_names in sorted(groups.items()):
        print(f"{group_name}:")
        for sn in step_names:
            print(f"  - {labels[sn].short()}")
    return 0


def build_label_parser(subparsers=None):
    if subparsers is None:
        parser = argparse.ArgumentParser(prog="patchwork-labels")
        sub = parser.add_subparsers(dest="label_cmd")
    else:
        parser = subparsers.add_parser("labels", help="Inspect step labels")
        sub = parser.add_subparsers(dest="label_cmd")

    # list
    p_list = sub.add_parser("list", help="List step labels")
    p_list.add_argument("config", help="Path to pipeline YAML")
    p_list.add_argument("--group", default=None, help="Filter by group name")
    p_list.set_defaults(func=cmd_list_labels)

    # groups
    p_groups = sub.add_parser("groups", help="List steps by group")
    p_groups.add_argument("config", help="Path to pipeline YAML")
    p_groups.set_defaults(func=cmd_list_groups)

    return parser


def main(argv: List[str] = None) -> int:
    parser = build_label_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
