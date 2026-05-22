"""Tests for the YAML config loader."""

import textwrap
import pytest

from patchwork.config import load_config, ConfigError, PipelineConfig, Step


MINIMAL_YAML = textwrap.dedent("""\
    name: my-pipeline
    steps:
      - name: build
        run: echo building
""")

FULL_YAML = textwrap.dedent("""\
    name: full-pipeline
    working_dir: /app
    env:
      APP_ENV: production
    steps:
      - name: migrate
        run: python manage.py migrate
        rollback: python manage.py migrate_rollback
        env:
          DB_URL: postgres://localhost/db
      - name: restart
        run: systemctl restart app
        ignore_errors: true
""")


@pytest.fixture
def yaml_file(tmp_path):
    def _write(content: str):
        p = tmp_path / "pipeline.yml"
        p.write_text(content)
        return str(p)
    return _write


def test_load_minimal_config(yaml_file):
    path = yaml_file(MINIMAL_YAML)
    config = load_config(path)
    assert isinstance(config, PipelineConfig)
    assert config.name == "my-pipeline"
    assert len(config.steps) == 1
    assert config.steps[0].name == "build"
    assert config.steps[0].run == "echo building"
    assert config.steps[0].rollback is None


def test_load_full_config(yaml_file):
    path = yaml_file(FULL_YAML)
    config = load_config(path)
    assert config.name == "full-pipeline"
    assert config.working_dir == "/app"
    assert config.env == {"APP_ENV": "production"}
    assert len(config.steps) == 2
    migrate = config.steps[0]
    assert migrate.rollback == "python manage.py migrate_rollback"
    assert migrate.env["DB_URL"] == "postgres://localhost/db"
    restart = config.steps[1]
    assert restart.ignore_errors is True


def test_missing_file_raises():
    with pytest.raises(ConfigError, match="not found"):
        load_config("/nonexistent/pipeline.yml")


def test_missing_name_raises(yaml_file):
    path = yaml_file("steps:\n  - name: x\n    run: echo x\n")
    with pytest.raises(ConfigError, match="'name'"):
        load_config(path)


def test_missing_steps_raises(yaml_file):
    path = yaml_file("name: p\n")
    with pytest.raises(ConfigError, match="'steps'"):
        load_config(path)


def test_step_missing_run_raises(yaml_file):
    path = yaml_file("name: p\nsteps:\n  - name: oops\n")
    with pytest.raises(ConfigError, match="'run'"):
        load_config(path)


def test_invalid_yaml_raises(yaml_file):
    path = yaml_file("name: p\nsteps: [unclosed")
    with pytest.raises(ConfigError, match="Failed to parse YAML"):
        load_config(path)
