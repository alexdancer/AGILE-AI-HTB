from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from token_tracker_harness import db
from token_tracker_harness.guardrails import load_guardrails
from token_tracker_harness.llm import LLMClient
from token_tracker_harness.routes import alarms, portal, proxy, sessions, tasks
from token_tracker_harness.settings import Settings


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    db.init_db(settings.database_path)
    app.state.guardrails = load_guardrails(settings.guardrails_path)
    if not hasattr(app.state, "llm_client"):
        app.state.llm_client = LLMClient()
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Token Tracker Harness", lifespan=_lifespan)
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
