"""Command-line entry point for patchwork-deploy."""

from __future__ import annotations

import argparse
import sys

from patchwork.config import ConfigError, load_config
from patchwork.executor import run_pipeline
from patchwork.printer import print_banner, print_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patchwork",
        description="Minimal deployment pipeline runner.",
    )
    parser.add_argument("config", help="Path to pipeline YAML config file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Simulate execution without running any commands",
    )
    parser.add_argument(
        "--workdir",
        default=None,
        metavar="DIR",
        help="Working directory for commands (default: current directory)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"[patchwork] Config error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"[patchwork] File not found: {exc}", file=sys.stderr)
        return 2

    print_banner(config.name, dry_run=args.dry_run)

    report = run_pipeline(config, dry_run=args.dry_run, workdir=args.workdir)

    print_report(report)

    return 0 if report.success else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
