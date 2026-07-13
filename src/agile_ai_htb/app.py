from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from agile_ai_htb import db, session_handoff, task_breakdown_handoff
from agile_ai_htb.guardrails import load_guardrails
from agile_ai_htb.llm import LLMClient
from agile_ai_htb.execution_backend import LocalExecutionBackend
from agile_ai_htb.routes import alarms, portal, proxy, react_shell, sessions, tasks
from agile_ai_htb.settings import Settings

@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    # Startup owns process-wide resources so tests can inject state before serving requests.
    db.init_db(settings.database_path)
    app.state.guardrails = load_guardrails(settings.guardrails_path)
    if not hasattr(app.state, "llm_client"):
        app.state.llm_client = LLMClient(settings)
    if settings.local_runner_enabled:
        app.state.execution_backend = LocalExecutionBackend(settings.database_path)
        # Touch the backend so startup fails early if the local runner cannot inspect its state.
        app.state.execution_backend.status()
    yield


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
    app.include_router(react_shell.router)
    app.include_router(session_handoff.router)
    app.include_router(task_breakdown_handoff.router)
    return app
