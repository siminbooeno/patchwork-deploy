"""CLI sub-commands for inspecting gate policies in a pipeline config."""
from __future__ import annotations

import argparse
import sys
from typing import List

from patchwork.config import PipelineConfig
from patchwork.step_gate import parse_gate, is_gated


def _load_gates(config: PipelineConfig):
    """Return list of (step_name, GatePolicy) for every step."""
    results = []
    for step in config.steps:
        raw = getattr(step, "gate", None)
        policy = parse_gate(raw)
        results.append((step.name, policy))
    return results


def cmd_list_gates(args: argparse.Namespace) -> int:
    """Print all steps that have a gate enabled."""
    from patchwork.config import load_config

    try:
        config = load_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    gates = [(name, p) for name, p in _load_gates(config) if is_gated(p)]

    if not gates:
        print("No gated steps found.")
        return 0

    print(f"{'STEP':<30} {'MESSAGE':<40} {'TIMEOUT':>10}")
    print("-" * 82)
    for name, policy in gates:
        timeout = f"{policy.timeout_seconds}s" if policy.timeout_seconds is not None else "none"
        print(f"{name:<30} {policy.message:<40} {timeout:>10}")
    return 0


def build_gate_parser(subparsers) -> None:
    gate_p = subparsers.add_parser("gates", help="Inspect gate policies in a pipeline")
    gate_sub = gate_p.add_subparsers(dest="gate_cmd")

    list_p = gate_sub.add_parser("list", help="List all gated steps")
    list_p.add_argument("config", help="Path to pipeline YAML")
    list_p.set_defaults(func=cmd_list_gates)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="patchwork-gates")
    subparsers = parser.add_subparsers(dest="command")
    build_gate_parser(subparsers)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
