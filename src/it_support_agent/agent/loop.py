"""The agent loop: call the model, run any tools it asks for, repeat."""

import logging
from typing import Any

from openai import OpenAI

from it_support_agent.agent.prompts import SYSTEM_PROMPT
from it_support_agent.core.exceptions import MaxStepsExceededError
from it_support_agent.tools.registry import ToolRegistry

log = logging.getLogger(__name__)


class Agent:
    def __init__(
        self,
        client: OpenAI,
        model: str,
        tools: ToolRegistry,
        system_prompt: str = SYSTEM_PROMPT,
        max_steps: int = 10,
    ) -> None:
        self.client = client
        self.model = model
        self.tools = tools
        self.max_steps = max_steps
        self.system_prompt = system_prompt
        self.messages: list[dict[str, Any]] = []
        self.reset()

    def reset(self) -> None:
        """Clear the conversation history."""
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def run(self, user_input: str) -> str:
        """Handle one user turn and return the final answer.

        History is kept across calls so follow-up questions have context.
        """
        self.messages.append({"role": "user", "content": user_input})

        for step in range(1, self.max_steps + 1):
            message = self._complete()
            self.messages.append(message.model_dump(exclude_none=True))

            if not message.tool_calls:
                return message.content or ""

            for call in message.tool_calls:
                log.info("step %d: %s(%s)", step, call.function.name, call.function.arguments)
                result = self.tools.execute(call.function.name, call.function.arguments)
                log.debug("step %d: %s -> %s", step, call.function.name, result)
                self.messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

        raise MaxStepsExceededError(f"No final answer after {self.max_steps} steps")

    def _complete(self):
        kwargs: dict[str, Any] = {"model": self.model, "messages": self.messages}
        if len(self.tools):
            kwargs["tools"] = self.tools.schemas()
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message
