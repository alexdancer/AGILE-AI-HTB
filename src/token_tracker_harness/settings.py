from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("harness.db")
    guardrails_path: Path = Path("guardrails.yaml")
    timezone: str = "local"
    provider_api_key_env: str = "PROVIDER_API_KEY"

    def __init__(
        self,
        database_path: Path | str | None = None,
        guardrails_path: Path | str | None = None,
        timezone: str | None = None,
        provider_api_key_env: str | None = None,
    ) -> None:
        object.__setattr__(
            self,
            "database_path",
            Path(database_path or os.getenv("TOKEN_TRACKER_DATABASE_PATH", "harness.db")),
        )
        object.__setattr__(
            self,
            "guardrails_path",
            Path(guardrails_path or os.getenv("TOKEN_TRACKER_GUARDRAILS_PATH", "guardrails.yaml")),
        )
        object.__setattr__(
            self,
            "timezone",
            timezone or os.getenv("TOKEN_TRACKER_TIMEZONE", "local"),
        )
        object.__setattr__(
            self,
            "provider_api_key_env",
            provider_api_key_env
            or os.getenv("TOKEN_TRACKER_PROVIDER_API_KEY_ENV", "PROVIDER_API_KEY"),
        )
