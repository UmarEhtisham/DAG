# app/config.py
# Central configuration file for the entire application.
# All settings are loaded from environment variables (.env file).
# Using Pydantic Settings ensures type safety and validation.

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    If a variable is missing from .env, an error will be raised at startup.
    """

    # ================================
    # LLM Provider
    # ================================
    openai_api_key: str

    # ================================
    # DataForSEO
    # ================================
    dataforseo_login: str = ""
    dataforseo_password: str = ""

    # "mock" uses fake data locally, "live" calls real DataForSEO API
    dataforseo_mode: str = "mock"

    # ================================
    # Database
    # ================================
    database_url: str

    # ================================
    # App Settings
    # ================================
    app_env: str = "development"

    # ================================
    # Retry Settings
    # ================================
    # Maximum number of retries on API failure
    max_retries: int = 3

    # Wait time in seconds before first retry (doubles each attempt)
    retry_backoff_seconds: int = 2

    # Maximum wait time for an external API call (seconds)
    api_timeout_seconds: int = 30

    # ================================
    # Observability
    # ================================
    log_level: str = "INFO"

    class Config:
        # Tell Pydantic to load values from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of Settings.
    lru_cache ensures .env is only read once — not on every function call.
    """
    return Settings()


# Single settings instance used across the entire app
settings = get_settings()