class AgentError(Exception):
    """Base error for the agent."""


class MaxStepsExceededError(AgentError):
    """The agent loop hit its step limit without a final answer."""


class ToolError(AgentError):
    """A tool failed in a way the model should be told about."""
