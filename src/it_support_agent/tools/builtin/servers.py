"""Server monitoring tools."""

import json
from typing import Annotated

from pydantic import Field

from it_support_agent.core.exceptions import ToolError
from it_support_agent.tools import tool

ServerId = Annotated[str, Field(description="The ID of the server, e.g., 'payment-server-01'.")]

# Hardcoded metrics until we connect to a real monitoring source.
MOCK_SERVER_METRICS: dict[str, dict[str, str]] = {
    # Scenario 1: High CPU (Needs Restart)
    "payment-server-01": {"cpu": "98%", "memory": "40%", "status": "Warning"},
    # Scenario 2: Healthy (No Action Needed)
    "db-node-02": {"cpu": "12%", "memory": "60%", "status": "Healthy"},
    # Scenario 3: High Memory Leak (Needs Restart or Escalation)
    "auth-service-03": {"cpu": "45%", "memory": "95%", "status": "Critical"},
    # Scenario 4: Network/Dependency Failure (Needs Escalation)
    "search-index-09": {"cpu": "10%", "memory": "15%", "status": "Error"},
    # Scenario 5: Completely Normal
    "frontend-node-04": {"cpu": "25%", "memory": "30%", "status": "Healthy"},
}

MOCK_SERVER_LOGS: dict[str, list[str]] = {
    "payment-server-01": [
        "[INFO] Request received /pay/v1",
        "[WARN] CPU threshold exceeded 90%",
        "[WARN] Thread pool exhaustion",
        "[CRITICAL] Process hung, not accepting new connections",
        "[ERROR] Timeout waiting for thread",
    ],
    "db-node-02": [
        "[INFO] Backup started",
        "[INFO] Backup completed successfully",
        "[INFO] User query executed in 12ms",
        "[INFO] Health check: OK",
        "[INFO] Replication sync active",
    ],
    "auth-service-03": [
        "[INFO] Token validated user_882",
        "[WARN] Garbage collection taking too long (>5s)",
        "[ERROR] java.lang.OutOfMemoryError: Java heap space",
        "[CRITICAL] Application crashing due to memory leak",
        "[INFO] Restarting context...",
    ],
    "search-index-09": [
        "[INFO] Indexing started",
        "[ERROR] Connection refused: elastic-cluster-main:9200",
        "[ERROR] Failed to write document ID 4432",
        "[CRITICAL] Dependency Unreachable: Search Engine is down",
        "[ERROR] Retrying in 30s...",
    ],
    "frontend-node-04": [
        "[INFO] GET /home 200 OK",
        "[INFO] GET /assets/logo.png 200 OK",
        "[INFO] GET /login 200 OK",
        "[INFO] GET /api/v1/status 200 OK",
        "[INFO] Health check passed",
    ],
}


def _unknown_server(server_id: str, known: dict) -> ToolError:
    return ToolError(f"Unknown server '{server_id}'. Known servers: {', '.join(known)}")


@tool
def get_server_health(server_id: ServerId) -> str:
    """Checks the current CPU and memory usage of a specific server."""
    metrics = MOCK_SERVER_METRICS.get(server_id)
    if metrics is None:
        raise _unknown_server(server_id, MOCK_SERVER_METRICS)
    return f"Server {server_id}: CPU {metrics['cpu']}, Memory {metrics['memory']}, Status {metrics['status']}"


@tool
def fetch_recent_logs(
    server_id: ServerId,
    lines: Annotated[int, Field(description="Number of log lines to fetch.")] = 5,
) -> str:
    """Retrieves the most recent log entries from a server to diagnose errors."""
    logs = MOCK_SERVER_LOGS.get(server_id)
    if logs is None:
        raise _unknown_server(server_id, MOCK_SERVER_LOGS)
    if lines < 1:
        raise ToolError("lines must be at least 1")
    return "\n".join(logs[-lines:])


@tool
def restart_service(server_id: ServerId) -> str:
    """Restarts the service on a server. Use this to recover from high CPU usage or a memory leak."""
    if server_id not in MOCK_SERVER_METRICS:
        raise _unknown_server(server_id, MOCK_SERVER_METRICS)
    print("-> TOOL: Restarting service...")
    return json.dumps({"status": "success", "message": f"Server {server_id} restarted successfully"})
