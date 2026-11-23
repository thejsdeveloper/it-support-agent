"""Settings loaded from the environment / .env file."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    model: str = "openai/gpt-4.1-mini"
    max_steps: int = 10
    log_level: str = "WARNING"

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set. Copy .env.example to .env and fill it in.")
        return cls(
            openrouter_api_key=api_key,
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", cls.openrouter_base_url),
            model=os.getenv("OPENROUTER_MODEL", cls.model),
            max_steps=int(os.getenv("AGENT_MAX_STEPS", cls.max_steps)),
            log_level=os.getenv("LOG_LEVEL", cls.log_level),
        )
