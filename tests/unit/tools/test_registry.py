import json

import pytest

from it_support_agent.tools import ToolRegistry, default_registry, tool
from tests.conftest import echo


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry([echo])


def test_schema_is_generated_from_args_model(registry):
    [schema] = registry.schemas()
    assert schema["function"]["name"] == "echo"
    assert schema["function"]["parameters"]["required"] == ["text"]


def test_execute_returns_result(registry):
    assert registry.execute("echo", '{"text": "hi"}') == "hi"


def test_non_string_results_are_json_encoded():
    @tool
    def info() -> dict:
        """Return a dict."""
        return {"ok": True}

    assert json.loads(ToolRegistry([info]).execute("info", "{}")) == {"ok": True}


@pytest.mark.parametrize(
    ("name", "args", "expected"),
    [
        ("missing", "{}", "Unknown tool"),
        ("echo", "{}", "Invalid arguments"),
        ("echo", "not json", "Invalid arguments"),
        ("echo", '{"text": "fail"}', "asked to fail"),
        ("echo", '{"text": "crash"}', "failed unexpectedly"),
    ],
)
def test_execute_returns_errors_instead_of_raising(registry, name, args, expected):
    assert expected in json.loads(registry.execute(name, args))["error"]


def test_duplicate_registration_rejected(registry):
    with pytest.raises(ValueError):
        registry.register(echo)


def test_default_registry_has_builtin_tools():
    registry = default_registry()
    assert "get_server_health" in registry
    assert "fetch_recent_logs" in registry
    assert "restart_service" in registry
    assert "escalate_to_engineer" in registry
