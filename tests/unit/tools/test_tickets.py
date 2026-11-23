import json
import re

import pytest

from it_support_agent.tools import ToolRegistry
from it_support_agent.tools.builtin.tickets import escalate_to_engineer


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry([escalate_to_engineer])


def escalate(registry, summary: str) -> dict:
    return json.loads(registry.execute("escalate_to_engineer", json.dumps({"summary": summary})))


def test_schema():
    params = escalate_to_engineer.schema()["function"]["parameters"]
    assert params["required"] == ["summary"]


def test_creates_ticket(registry, capsys):
    result = escalate(registry, "search-index-09 cannot reach elastic-cluster-main")
    assert result["status"] == "success"
    assert re.fullmatch(r"INC-[0-9A-F]{8}", result["ticket_id"])
    assert result["ticket_id"] in result["message"]
    assert "-> TOOL: Escalating to human..." in capsys.readouterr().out


def test_ticket_ids_are_unique(registry):
    assert escalate(registry, "a")["ticket_id"] != escalate(registry, "b")["ticket_id"]


def test_empty_summary_rejected(registry, capsys):
    assert "must not be empty" in escalate(registry, "   ")["error"]
    assert capsys.readouterr().out == ""
