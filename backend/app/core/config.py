from __future__ import annotations

import os
from dataclasses import dataclass, field


def _origins_from_environment() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True, slots=True)
class Settings:
    upstage_api_key: str | None = field(default_factory=lambda: os.getenv("UPSTAGE_API_KEY"))
    upstage_model: str = field(default_factory=lambda: os.getenv("UPSTAGE_MODEL", "solar-pro4"))
    upstage_base_url: str = field(
        default_factory=lambda: os.getenv("UPSTAGE_BASE_URL", "https://api.upstage.ai/v1")
    )
    upstage_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("UPSTAGE_TIMEOUT_SECONDS", "30"))
    )
    solar_mode: str = field(default_factory=lambda: os.getenv("SOLAR_MODE", "fake").lower())
    cors_allow_origins: list[str] = field(default_factory=_origins_from_environment)


def get_settings() -> Settings:
    return Settings()
