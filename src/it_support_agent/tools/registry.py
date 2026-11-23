"""Holds tools, exposes their schemas, and dispatches tool calls safely."""

import json
import logging
from collections.abc import Iterable
from typing import Any

from pydantic import ValidationError

from it_support_agent.core.exceptions import ToolError
from it_support_agent.tools.decorator import Tool

log = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self, tools: Iterable[Tool] = ()) -> None:
        self._tools: dict[str, Tool] = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self._tools.values()]

    def execute(self, name: str, raw_args: str) -> str:
        """Run a tool call and return the text the model will see.

        A string result is passed through unchanged; anything else (dict, list,
        number) is JSON-encoded. Failures are returned as {"error": ...} rather
        than raised, so the model can see what went wrong and recover.
        """
        tool = self._tools.get(name)
        if tool is None:
            return _error(f"Unknown tool: {name}")
        try:
            args = tool.args_model.model_validate_json(raw_args or "{}")
        except ValidationError as exc:
            return _error(f"Invalid arguments: {exc.errors(include_url=False)}")
        try:
            result = tool.fn(**dict(args))
        except ToolError as exc:
            return _error(str(exc))
        except Exception:
            log.exception("Tool %s crashed", name)
            return _error(f"Tool {name} failed unexpectedly")
        if isinstance(result, str):
            return result
        return json.dumps(result, default=str)


def _error(message: str) -> str:
    return json.dumps({"error": message})


def default_registry() -> ToolRegistry:
    from it_support_agent.tools.builtin import BUILTIN_TOOLS

    return ToolRegistry(BUILTIN_TOOLS)
