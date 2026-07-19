"""
Central configuration. Every other module reads settings from here —
never call os.getenv() scattered across the codebase.
"""
import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("autopr.config")


class ConfigError(Exception):
    """Raised when required environment variables are missing."""


@dataclass(frozen=True)
class Settings:
    github_token: str
    groq_api_key: str
    groq_model: str = "groq/llama-3.3-70b-versatile"


def load_settings() -> Settings:
    github_token = os.getenv("GITHUB_TOKEN")
    groq_api_key = os.getenv("GROQ_API_KEY")

    missing = [
        name for name, val in
        [("GITHUB_TOKEN", github_token), ("GROQ_API_KEY", groq_api_key)]
        if not val
    ]
    if missing:
        raise ConfigError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Check your .env file."
        )

    logger.info("Configuration loaded successfully.")
    return Settings(github_token=github_token, groq_api_key=groq_api_key)


settings = load_settings()