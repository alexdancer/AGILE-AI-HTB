from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from agile_ai_htb import db
from agile_ai_htb.guardrails import load_guardrails
from agile_ai_htb.llm import LLMClient
from agile_ai_htb.execution_backend import LocalExecutionBackend
from agile_ai_htb.routes import alarms, portal, proxy, sessions, tasks
from agile_ai_htb.settings import Settings

_PROVIDER_KEY_ENVS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "COHERE_API_KEY", "GROQ_API_KEY")


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    db.init_db(settings.database_path)
    app.state.guardrails = load_guardrails(settings.guardrails_path)
    if not hasattr(app.state, "llm_client"):
        app.state.llm_client = LLMClient()
    if settings.local_runner_enabled:
        app.state.execution_backend = LocalExecutionBackend(settings.database_path)
        app.state.execution_backend.status()
    _bridge_provider_key(settings)
    yield


def _bridge_provider_key(settings: Settings) -> None:
    """Copy the control-plane key to provider-specific env vars so LiteLLM finds it.

    AGILE-AI-HTB's control-plane model auth is separate from Worker Harness
    auth. The legacy provider key env remains a compatibility fallback only.
    """
    key_value = os.getenv(settings.control_plane_api_key_env) or os.getenv(settings.provider_api_key_env)
    if not key_value:
        return
    for env_name in _PROVIDER_KEY_ENVS:
        if not os.getenv(env_name):
            os.environ[env_name] = key_value


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="AGILE-AI-HTB", lifespan=_lifespan)
    app.state.settings = settings or Settings()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(sessions.router)
    app.include_router(tasks.router)
    app.include_router(alarms.router)
    app.include_router(proxy.router)
    app.include_router(portal.router)
    return app
