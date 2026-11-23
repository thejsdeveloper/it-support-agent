import pytest

from it_support_agent.agent import Agent
from it_support_agent.core.exceptions import MaxStepsExceededError
from it_support_agent.tools import ToolRegistry
from tests.conftest import echo, text, tool_call


def make_agent(client, max_steps=5):
    return Agent(client=client, model="test-model", tools=ToolRegistry([echo]), max_steps=max_steps)


def test_returns_text_when_no_tool_calls(fake_client):
    client = fake_client([text("hello")])
    assert make_agent(client).run("hi") == "hello"
    assert "tools" in client.requests[0]


def test_runs_tool_then_answers(fake_client):
    client = fake_client([tool_call("echo", {"text": "pong"}), text("done")])
    agent = make_agent(client)

    assert agent.run("ping") == "done"

    tool_msg = agent.messages[-2]
    assert tool_msg["role"] == "tool"
    assert tool_msg["tool_call_id"] == "call_1"
    assert tool_msg["content"] == "pong"
    # the second request must include the tool result
    assert client.requests[1]["messages"][-1]["role"] == "tool"


def test_history_kept_across_turns(fake_client):
    client = fake_client([text("one"), text("two")])
    agent = make_agent(client)
    agent.run("first")
    agent.run("second")
    roles = [m["role"] for m in client.requests[1]["messages"]]
    assert roles == ["system", "user", "assistant", "user"]


def test_max_steps_exceeded(fake_client):
    client = fake_client([tool_call("echo", {"text": "x"})] * 3)
    with pytest.raises(MaxStepsExceededError):
        make_agent(client, max_steps=3).run("loop forever")
