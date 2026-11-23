"""OpenRouter client (OpenAI-compatible API)."""

from openai import OpenAI

from it_support_agent.core.config import Settings


def make_client(settings: Settings) -> OpenAI:
    return OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        default_headers={"X-Title": "it-support-agent"},
    )
