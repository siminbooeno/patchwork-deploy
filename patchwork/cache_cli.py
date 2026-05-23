"""CLI sub-commands for managing the step cache."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from patchwork.step_cache import StepCache, _DEFAULT_CACHE_FILE


def cmd_show(args: argparse.Namespace) -> int:
    """Print current cache contents."""
    cache = StepCache.load(args.cache_file)
    entries = cache._entries
    if not entries:
        print("Cache is empty.")
        return 0
    print(f"{'STEP':<30} {'HASH':<18} {'EXIT'}")
    print("-" * 54)
    for name, entry in sorted(entries.items()):
        status = "OK" if entry.exit_code == 0 else f"FAIL({entry.exit_code})"
        print(f"{name:<30} {entry.command_hash:<18} {status}")
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    """Wipe all cache entries."""
    p = Path(args.cache_file)
    if not p.exists():
        print("Nothing to clear.")
        return 0
    cache = StepCache.load(p)
    cache.clear()
    cache.save()
    print(f"Cache cleared ({args.cache_file}).")
    return 0


def cmd_invalidate(args: argparse.Namespace) -> int:
    """Remove a single step from the cache."""
    cache = StepCache.load(args.cache_file)
    if args.step not in cache._entries:
        print(f"Step '{args.step}' not found in cache.")
        return 1
    cache.invalidate(args.step)
    cache.save()
    print(f"Invalidated cache entry for '{args.step}'.")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export cache as JSON."""
    cache = StepCache.load(args.cache_file)
    data = {k: v.as_dict() for k, v in cache._entries.items()}
    print(json.dumps(data, indent=2))
    return 0


def build_cache_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("cache", help="Manage the step cache")
    p.add_argument(
        "--cache-file",
        default=_DEFAULT_CACHE_FILE,
        metavar="FILE",
        help="Path to cache file (default: %(default)s)",
    )
    sub = p.add_subparsers(dest="cache_cmd", required=True)

    sub.add_parser("show", help="Display cached steps")
    sub.add_parser("clear", help="Remove all cache entries")
    inv = sub.add_parser("invalidate", help="Remove one step from cache")
    inv.add_argument("step", help="Step name to invalidate")
    sub.add_parser("export", help="Export cache as JSON")


def run_cache_command(args: argparse.Namespace) -> int:
    dispatch = {
        "show": cmd_show,
        "clear": cmd_clear,
        "invalidate": cmd_invalidate,
        "export": cmd_export,
    }
    fn = dispatch.get(args.cache_cmd)
    if fn is None:
        print(f"Unknown cache sub-command: {args.cache_cmd}")
        return 2
    return fn(args)
