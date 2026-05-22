"""Tests for patchwork.env_resolver."""

import pytest

from patchwork.env_resolver import (
    ResolutionError,
    resolve,
    resolve_dict,
    resolve_step_command,
)

_ENV = {"APP_ENV": "production", "PORT": "8080", "HOST": "example.com"}


def test_no_placeholders_returns_original():
    assert resolve("echo hello", _ENV) == "echo hello"


def test_single_variable_substituted():
    assert resolve("deploy to ${APP_ENV}", _ENV) == "deploy to production"


def test_multiple_variables_substituted():
    result = resolve("${HOST}:${PORT}", _ENV)
    assert result == "example.com:8080"


def test_default_used_when_variable_missing():
    result = resolve("${MISSING:fallback}", _ENV)
    assert result == "fallback"


def test_default_empty_string():
    result = resolve("prefix_${MISSING:}_suffix", _ENV)
    assert result == "prefix__suffix"


def test_present_variable_overrides_default():
    result = resolve("${PORT:9999}", _ENV)
    assert result == "8080"


def test_missing_required_variable_raises():
    with pytest.raises(ResolutionError) as exc_info:
        resolve("${UNDEFINED_VAR}", _ENV)
    assert exc_info.value.variable == "UNDEFINED_VAR"


def test_resolution_error_str():
    err = ResolutionError("MY_VAR")
    assert "MY_VAR" in str(err)


def test_resolve_step_command_delegates():
    cmd = resolve_step_command("./deploy.sh ${APP_ENV}", _ENV)
    assert cmd == "./deploy.sh production"


def test_resolve_dict_resolves_all_values():
    data = {"url": "http://${HOST}:${PORT}", "env": "${APP_ENV}"}
    result = resolve_dict(data, _ENV)
    assert result == {"url": "http://example.com:8080", "env": "production"}


def test_resolve_dict_raises_on_missing_required():
    with pytest.raises(ResolutionError):
        resolve_dict({"key": "${NO_SUCH_VAR}"}, _ENV)


def test_uses_os_environ_by_default(monkeypatch):
    monkeypatch.setenv("PW_TEST_VAR", "live_value")
    assert resolve("${PW_TEST_VAR}") == "live_value"
