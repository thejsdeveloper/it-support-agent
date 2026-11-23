import json

import pytest

from it_support_agent.tools import ToolRegistry
from it_support_agent.tools.builtin.servers import fetch_recent_logs, get_server_health, restart_service


def call(registry, name, **args) -> str:
    return registry.execute(name, json.dumps(args))


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry([get_server_health, fetch_recent_logs, restart_service])


def test_schema():
    params = get_server_health.schema()["function"]["parameters"]
    assert params["required"] == ["server_id"]


@pytest.mark.parametrize(
    ("server_id", "expected"),
    [
        ("payment-server-01", "CPU 98%, Memory 40%, Status Warning"),
        ("db-node-02", "CPU 12%, Memory 60%, Status Healthy"),
        ("auth-service-03", "CPU 45%, Memory 95%, Status Critical"),
        ("search-index-09", "CPU 10%, Memory 15%, Status Error"),
        ("frontend-node-04", "CPU 25%, Memory 30%, Status Healthy"),
    ],
)
def test_known_servers(registry, server_id, expected):
    assert call(registry, "get_server_health", server_id=server_id) == f"Server {server_id}: {expected}"


def test_unknown_server_returns_error(registry):
    result = json.loads(call(registry, "get_server_health", server_id="nope"))
    assert "Unknown server 'nope'" in result["error"]


def test_logs_schema():
    params = fetch_recent_logs.schema()["function"]["parameters"]
    assert params["required"] == ["server_id"]
    assert params["properties"]["lines"]["default"] == 5


def test_logs_default_returns_all_five(registry):
    result = call(registry, "fetch_recent_logs", server_id="payment-server-01")
    assert result.splitlines() == [
        "[INFO] Request received /pay/v1",
        "[WARN] CPU threshold exceeded 90%",
        "[WARN] Thread pool exhaustion",
        "[CRITICAL] Process hung, not accepting new connections",
        "[ERROR] Timeout waiting for thread",
    ]


def test_logs_returns_last_n(registry):
    result = call(registry, "fetch_recent_logs", server_id="auth-service-03", lines=2)
    assert result.splitlines() == [
        "[CRITICAL] Application crashing due to memory leak",
        "[INFO] Restarting context...",
    ]


def test_logs_more_than_available_returns_all(registry):
    result = call(registry, "fetch_recent_logs", server_id="db-node-02", lines=50)
    assert len(result.splitlines()) == 5


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ({"server_id": "nope"}, "Unknown server 'nope'"),
        ({"server_id": "db-node-02", "lines": 0}, "lines must be at least 1"),
        ({"server_id": "db-node-02", "lines": "many"}, "Invalid arguments"),
    ],
)
def test_logs_errors(registry, args, expected):
    assert expected in json.loads(call(registry, "fetch_recent_logs", **args))["error"]


def test_restart_service(registry, capsys):
    result = json.loads(call(registry, "restart_service", server_id="payment-server-01"))
    assert result == {"status": "success", "message": "Server payment-server-01 restarted successfully"}
    assert "-> TOOL: Restarting service..." in capsys.readouterr().out


def test_restart_unknown_server(registry, capsys):
    result = json.loads(call(registry, "restart_service", server_id="nope"))
    assert "Unknown server 'nope'" in result["error"]
    assert capsys.readouterr().out == ""
