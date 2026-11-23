"""Command-line entry point: one-shot (`it-support-agent "question"`) or interactive REPL."""

import argparse

from it_support_agent.agent import Agent
from it_support_agent.core.config import Settings
from it_support_agent.core.exceptions import AgentError
from it_support_agent.core.logging import setup_logging
from it_support_agent.llm import make_client
from it_support_agent.tools import default_registry


def build_agent(settings: Settings) -> Agent:
    return Agent(
        client=make_client(settings),
        model=settings.model,
        tools=default_registry(),
        max_steps=settings.max_steps,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="it-support-agent", description=__doc__)
    parser.add_argument("prompt", nargs="*", help="Question to ask. Omit for interactive mode.")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    setup_logging(settings.log_level)
    agent = build_agent(settings)

    if args.prompt:
        print(agent.run(" ".join(args.prompt)))
        return 0

    print("IT support agent. Type 'exit' to quit, 'reset' to clear history.")
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if user_input in {"exit", "quit"}:
            return 0
        if user_input == "reset":
            agent.reset()
            continue
        if not user_input:
            continue
        try:
            print(agent.run(user_input))
        except AgentError as exc:
            print(f"error: {exc}")
