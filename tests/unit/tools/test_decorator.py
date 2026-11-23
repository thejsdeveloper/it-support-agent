import pytest

from it_support_agent.tools import tool


def test_builds_tool_from_function():
    @tool
    def ping(host: str, count: int = 4) -> str:
        """Ping a host."""
        return f"{host} x{count}"

    assert ping.name == "ping"
    assert ping.description == "Ping a host."
    params = ping.schema()["function"]["parameters"]
    assert params["properties"]["host"]["type"] == "string"
    assert params["properties"]["count"]["default"] == 4
    assert params["required"] == ["host"]
    assert ping("a.com") == "a.com x4"  # still callable like a normal function


def test_requires_docstring():
    with pytest.raises(ValueError, match="docstring"):

        @tool
        def nodoc(x: str) -> str:
            return x


def test_requires_type_hints():
    with pytest.raises(TypeError, match="type hint"):

        @tool
        def nohint(x) -> str:
            """Doc."""
            return x


def test_annotated_descriptions_reach_schema():
    from typing import Annotated

    from pydantic import Field

    @tool
    def ping(host: Annotated[str, Field(description="Host to ping.")]) -> str:
        """Ping a host."""
        return host

    props = ping.schema()["function"]["parameters"]["properties"]
    assert props["host"]["description"] == "Host to ping."
    assert ping("a.com") == "a.com"
