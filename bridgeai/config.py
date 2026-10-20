"""Environment configuration. Secrets stay in the environment and are never logged."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://llm.c.singularitynet.io/v1"
DEFAULT_MODEL = "asi1-mini"


def load_local_env() -> None:
    """Load a local .env file without overriding variables already set."""
    load_dotenv(ROOT / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    enabled: bool

    @property
    def live_available(self) -> bool:
        return self.enabled and bool(self.api_key)


def _flag(value: str | None, default: bool = True) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    """Read provider settings from the environment on each call."""
    load_local_env()
    return Settings(
        api_key=os.getenv("ASI_API_KEY", "").strip(),
        base_url=os.getenv("OMEGA_LLM_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL,
        model=os.getenv("OMEGA_LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        enabled=_flag(os.getenv("OMEGA_LLM_ENABLED"), default=True),
    )


def provider_available() -> bool:
    return get_settings().live_available


def public_provider_status() -> dict[str, object]:
    """Status safe to show in the interface. The API key is never included."""
    settings = get_settings()
    available = settings.live_available
    return {
        "available": available,
        "enabled_flag": settings.enabled,
        "model": settings.model if available else None,
        "provider": "omega-asi" if available else None,
    }


@lru_cache(maxsize=1)
def project_root() -> Path:
    return ROOT
