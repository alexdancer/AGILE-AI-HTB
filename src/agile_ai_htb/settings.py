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
    estimator_model: str = "gpt-4o-mini"
    portal_token_env: str = "TOKEN_TRACKER_PORTAL_TOKEN"
    portal_cookie_secure: bool = False

    def __init__(
        self,
        database_path: Path | str | None = None,
        guardrails_path: Path | str | None = None,
        timezone: str | None = None,
        provider_api_key_env: str | None = None,
        estimator_model: str | None = None,
        portal_token_env: str | None = None,
        portal_cookie_secure: bool | None = None,
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
        object.__setattr__(
            self,
            "estimator_model",
            estimator_model or os.getenv("TOKEN_TRACKER_ESTIMATOR_MODEL", "gpt-4o-mini"),
        )
        object.__setattr__(
            self,
            "portal_token_env",
            portal_token_env or os.getenv("TOKEN_TRACKER_PORTAL_TOKEN_ENV", "TOKEN_TRACKER_PORTAL_TOKEN"),
        )
        object.__setattr__(
            self,
            "portal_cookie_secure",
            _env_bool("TOKEN_TRACKER_PORTAL_COOKIE_SECURE")
            if portal_cookie_secure is None
            else portal_cookie_secure,
        )


def _env_bool(name: str) -> bool:
    return os.getenv(name, "").lower() in {"1", "true", "yes", "on"}
