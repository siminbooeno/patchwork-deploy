"""Command-line interface for patchwork-deploy."""
from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from typing import List, Optional

from patchwork.config import ConfigError, load_config
from patchwork.executor import run_pipeline
from patchwork.printer import print_banner, print_report
from patchwork.step_filter import apply_filter, parse_filter_criteria
from patchwork.validator import validate


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="patchwork",
        description="Minimal deployment pipeline runner",
    )
    parser.add_argument("config", help="Path to pipeline YAML config")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print steps without executing them",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        metavar="TAG",
        default=None,
        help="Only run steps that have at least one of these tags",
    )
    parser.add_argument(
        "--names",
        nargs="+",
        metavar="NAME",
        default=None,
        help="Only run steps with these exact names",
    )
    parser.add_argument(
        "--skip-tags",
        nargs="+",
        metavar="TAG",
        default=None,
        dest="skip_tags",
        help="Skip steps that carry any of these tags",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args: Namespace = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"[patchwork] error: {exc}", file=sys.stderr)
        return 2

    result = validate(config)
    if not result.ok:
        for msg in result.errors:
            print(f"[patchwork] validation error: {msg}", file=sys.stderr)
        return 2

    # Apply step filters when any filter flag was provided
    criteria = parse_filter_criteria(
        tags=args.tags,
        names=args.names,
        skip_tags=args.skip_tags,
    )
    config.steps = apply_filter(config.steps, criteria)

    print_banner(config, dry_run=args.dry_run)
    report = run_pipeline(config, dry_run=args.dry_run)
    print_report(report)
    return 0 if report.success else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
