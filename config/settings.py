"""
config/settings.py
==================
Centralized configuration management.
Loads all environment variables and makes them available project-wide.
"""

import os
from dotenv import load_dotenv

# Load .env file at startup
load_dotenv()


class Settings:
    """
    Single source of truth for all configuration.

    Workshop Note:
        This pattern separates config from code — a best practice
        for any AI application going to production.
    """

    # ── Google Gemini ──────────────────────────────────────────
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # ── LangSmith (Developer Debugging) ───────────────────────
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "IT-Helpdesk-Workshop")
    LANGCHAIN_ENDPOINT: str = os.getenv(
        "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
    )

    # ── LangFuse (Production Observability) ───────────────────
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # ── Application ───────────────────────────────────────────
    APP_NAME: str = os.getenv("APP_NAME", "AI IT Helpdesk")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    @property
    def langsmith_enabled(self) -> bool:
        """True when LangSmith tracing is configured and enabled."""
        return bool(
            self.LANGCHAIN_API_KEY and self.LANGCHAIN_TRACING_V2.lower() == "true"
        )

    @property
    def langfuse_enabled(self) -> bool:
        """True when LangFuse keys are configured."""
        return bool(self.LANGFUSE_PUBLIC_KEY and self.LANGFUSE_SECRET_KEY)

    def apply_langsmith_env(self):
        """
        Apply LangSmith environment variables so LangChain auto-traces.

        Workshop Note:
            LangSmith tracing is AUTOMATIC once these env vars are set.
            Every LangChain LLM call, chain, and tool will be traced.
        """
        if self.langsmith_enabled:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.LANGCHAIN_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = self.LANGCHAIN_PROJECT
            os.environ["LANGCHAIN_ENDPOINT"] = self.LANGCHAIN_ENDPOINT

    def status_report(self) -> dict:
        """Return a dict showing which integrations are active."""
        return {
            "google_api": bool(self.GOOGLE_API_KEY),
            "langsmith": self.langsmith_enabled,
            "langfuse": self.langfuse_enabled,
            "model": self.GEMINI_MODEL,
            "environment": self.APP_ENV,
        }


# Global singleton — import this everywhere
settings = Settings()

# Apply LangSmith environment on import (auto-enables tracing)
settings.apply_langsmith_env()
