"""Tests for patchwork.config (including retry integration)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from patchwork.config import ConfigError, PipelineConfig, Step, load_config
from patchwork.retry import RetryPolicy


@pytest.fixture
def yaml_file(tmp_path: Path):
    def _write(content: str) -> str:
        p = tmp_path / "pipeline.yml"
        p.write_text(textwrap.dedent(content))
        return str(p)
    return _write


def test_load_minimal_config(yaml_file):
    path = yaml_file("""
        pipeline: minimal
        steps:
          - name: hello
            command: echo hello
    """)
    cfg = load_config(path)
    assert isinstance(cfg, PipelineConfig)
    assert cfg.name == "minimal"
    assert len(cfg.steps) == 1


def test_load_full_config(yaml_file):
    path = yaml_file("""
        pipeline: full
        notify: slack
        audit_log: /tmp/audit.jsonl
        summary_file: /tmp/summary.json
        steps:
          - name: build
            command: make build
            tags: [ci]
            rollback: make clean
            env:
              NODE_ENV: production
    """)
    cfg = load_config(path)
    assert cfg.notify == "slack"
    assert cfg.audit_log == "/tmp/audit.jsonl"
    step = cfg.steps[0]
    assert step.tags == ["ci"]
    assert step.rollback == "make clean"
    assert step.env == {"NODE_ENV": "production"}


def test_missing_file_raises():
    with pytest.raises(ConfigError, match="not found"):
        load_config("/nonexistent/path.yml")


def test_missing_pipeline_name_raises(yaml_file):
    path = yaml_file("""
        steps:
          - name: x
            command: echo x
    """)
    with pytest.raises(ConfigError, match="pipeline"):
        load_config(path)


def test_step_missing_name_raises(yaml_file):
    path = yaml_file("""
        pipeline: p
        steps:
          - command: echo hi
    """)
    with pytest.raises(ConfigError, match="name"):
        load_config(path)


def test_step_missing_command_raises(yaml_file):
    path = yaml_file("""
        pipeline: p
        steps:
          - name: no-cmd
    """)
    with pytest.raises(ConfigError, match="command"):
        load_config(path)


def test_retry_int_shorthand_parsed(yaml_file):
    path = yaml_file("""
        pipeline: p
        steps:
          - name: flaky
            command: echo hi
            retry: 3
    """)
    cfg = load_config(path)
    assert cfg.steps[0].retry == RetryPolicy(max_attempts=3)


def test_retry_dict_parsed(yaml_file):
    path = yaml_file("""
        pipeline: p
        steps:
          - name: flaky
            command: echo hi
            retry:
              attempts: 4
              delay: 1.5
              backoff: 2.0
    """)
    cfg = load_config(path)
    r = cfg.steps[0].retry
    assert r.max_attempts == 4
    assert r.delay_seconds == 1.5
    assert r.backoff_factor == 2.0


def test_default_retry_is_single_attempt(yaml_file):
    path = yaml_file("""
        pipeline: p
        steps:
          - name: s
            command: echo s
    """)
    cfg = load_config(path)
    assert cfg.steps[0].retry == RetryPolicy(max_attempts=1)
