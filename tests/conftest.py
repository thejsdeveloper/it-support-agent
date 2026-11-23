"""Fake OpenAI client so agent tests run offline and deterministically."""

import json
from types import SimpleNamespace
from typing import Any

import pytest


class FakeMessage(SimpleNamespace):
    def model_dump(self, exclude_none: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            data["tool_calls"] = [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {"name": c.function.name, "arguments": c.function.arguments},
                }
                for c in self.tool_calls
            ]
        return {k: v for k, v in data.items() if v is not None} if exclude_none else data


def text(content: str) -> FakeMessage:
    return FakeMessage(content=content, tool_calls=None)


def tool_call(name: str, args: dict | None = None, call_id: str = "call_1") -> FakeMessage:
    fn = SimpleNamespace(name=name, arguments=json.dumps(args or {}))
    return FakeMessage(content=None, tool_calls=[SimpleNamespace(id=call_id, function=fn)])


class FakeClient:
    """Returns scripted messages in order and records each request."""

    def __init__(self, replies: list[FakeMessage]) -> None:
        self._replies = iter(replies)
        self.requests: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: Any) -> SimpleNamespace:
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return SimpleNamespace(choices=[SimpleNamespace(message=next(self._replies))])


@pytest.fixture
def fake_client():
    return FakeClient


# --- test-only tool ---------------------------------------------------------

from it_support_agent.core.exceptions import ToolError  # noqa: E402
from it_support_agent.tools import tool  # noqa: E402


@tool
def echo(text: str) -> str:
    """Echo text back."""
    if text == "fail":
        raise ToolError("asked to fail")
    if text == "crash":
        raise RuntimeError("boom")
    return text
