"""Tests for patchwork.cli."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from patchwork.cli import main


@pytest.fixture()
def simple_yaml(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        name: cli-test
        rollback_on_failure: false
        steps:
          - name: greet
            command: echo hello
    """)
    p = tmp_path / "pipeline.yml"
    p.write_text(content)
    return p


@pytest.fixture()
def failing_yaml(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        name: failing-pipeline
        rollback_on_failure: false
        steps:
          - name: boom
            command: exit 1
    """)
    p = tmp_path / "failing.yml"
    p.write_text(content)
    return p


def test_cli_success(simple_yaml: Path):
    code = main([str(simple_yaml)])
    assert code == 0


def test_cli_dry_run(simple_yaml: Path):
    code = main([str(simple_yaml), "--dry-run"])
    assert code == 0


def test_cli_failure_returns_nonzero(failing_yaml: Path):
    code = main([str(failing_yaml)])
    assert code == 1


def test_cli_missing_file_returns_2():
    code = main(["nonexistent_file.yml"])
    assert code == 2


def test_cli_workdir(simple_yaml: Path, tmp_path: Path):
    code = main([str(simple_yaml), "--workdir", str(tmp_path)])
    assert code == 0
