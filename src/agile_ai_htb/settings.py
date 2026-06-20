from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("harness.db")
    guardrails_path: Path = Path("guardrails.yaml")
    timezone: str = "local"
    control_plane_provider: str = "openai"
    control_plane_model: str = "gpt-4o-mini"
    control_plane_api_key_env: str = "AGILE_AI_HTB_CONTROL_API_KEY"
    control_plane_base_url: str = ""
    provider_api_key_env: str = "PROVIDER_API_KEY"
    estimator_model: str = "gpt-4o-mini"
    portal_token_env: str = "TOKEN_TRACKER_PORTAL_TOKEN"
    portal_cookie_secure: bool = False
    local_runner_enabled: bool = False

    def __init__(
        self,
        database_path: Path | str | None = None,
        guardrails_path: Path | str | None = None,
        timezone: str | None = None,
        control_plane_provider: str | None = None,
        control_plane_model: str | None = None,
        control_plane_api_key_env: str | None = None,
        control_plane_base_url: str | None = None,
        provider_api_key_env: str | None = None,
        estimator_model: str | None = None,
        portal_token_env: str | None = None,
        portal_cookie_secure: bool | None = None,
        local_runner_enabled: bool | None = None,
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
        legacy_provider_env = provider_api_key_env or os.getenv(
            "TOKEN_TRACKER_PROVIDER_API_KEY_ENV", "PROVIDER_API_KEY"
        )
        resolved_control_api_env = (
            control_plane_api_key_env
            or os.getenv("AGILE_AI_HTB_CONTROL_API_KEY_ENV")
            or os.getenv("TOKEN_TRACKER_CONTROL_PLANE_API_KEY_ENV")
            or "AGILE_AI_HTB_CONTROL_API_KEY"
        )
        resolved_control_model = (
            control_plane_model
            or os.getenv("AGILE_AI_HTB_CONTROL_MODEL")
            or os.getenv("TOKEN_TRACKER_CONTROL_PLANE_MODEL")
            or estimator_model
            or os.getenv("TOKEN_TRACKER_ESTIMATOR_MODEL", "gpt-4o-mini")
        )
        object.__setattr__(
            self,
            "control_plane_provider",
            control_plane_provider
            or os.getenv("AGILE_AI_HTB_CONTROL_PROVIDER")
            or os.getenv("TOKEN_TRACKER_CONTROL_PLANE_PROVIDER", "openai"),
        )
        object.__setattr__(self, "control_plane_model", resolved_control_model)
        object.__setattr__(self, "control_plane_api_key_env", resolved_control_api_env)
        object.__setattr__(
            self,
            "control_plane_base_url",
            control_plane_base_url
            or os.getenv("AGILE_AI_HTB_CONTROL_BASE_URL")
            or os.getenv("TOKEN_TRACKER_CONTROL_PLANE_BASE_URL", ""),
        )
        object.__setattr__(
            self,
            "provider_api_key_env",
            legacy_provider_env,
        )
        object.__setattr__(
            self,
            "estimator_model",
            resolved_control_model,
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
        object.__setattr__(
            self,
            "local_runner_enabled",
            _env_bool("TOKEN_TRACKER_LOCAL_RUNNER")
            if local_runner_enabled is None
            else local_runner_enabled,
        )


def _env_bool(name: str) -> bool:
    return os.getenv(name, "").lower() in {"1", "true", "yes", "on"}
