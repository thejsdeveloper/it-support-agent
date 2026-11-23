"""The @tool decorator: turns a plain function into a tool the agent can call.

    @tool
    def get_server_health(server_id: str) -> str:
        \"\"\"Returns CPU and Memory usage for a given server.\"\"\"
        ...

The function name becomes the tool name, the docstring becomes the description,
and the type hints become the JSON schema (built with pydantic, which also
validates the arguments the model sends back).
"""

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, create_model


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    fn: Callable[..., Any]
    args_model: type[BaseModel]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Calling the tool still calls the original function."""
        return self.fn(*args, **kwargs)

    def schema(self) -> dict[str, Any]:
        """OpenAI function-calling schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.args_model.model_json_schema(),
            },
        }


def tool(fn: Callable[..., Any]) -> Tool:
    description = inspect.getdoc(fn)
    if not description:
        raise ValueError(f"Tool '{fn.__name__}' needs a docstring; it is the description the model sees.")

    fields: dict[str, Any] = {}
    for param in inspect.signature(fn).parameters.values():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            raise TypeError(f"Tool '{fn.__name__}' cannot use *args or **kwargs.")
        if param.annotation is param.empty:
            raise TypeError(f"Tool '{fn.__name__}': parameter '{param.name}' needs a type hint.")
        default = ... if param.default is param.empty else param.default
        fields[param.name] = (param.annotation, default)

    args_model = create_model(f"{fn.__name__}_args", **fields)
    return Tool(name=fn.__name__, description=description, fn=fn, args_model=args_model)
