from __future__ import annotations

import os
import secrets

from fastapi import HTTPException, Request


def require_portal_auth(request: Request) -> None:
    token_env = request.app.state.settings.portal_token_env
    expected_token = os.getenv(token_env, "")
    authorization = request.headers.get("authorization", "")
    prefix = "Bearer "
    if not expected_token or not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="missing portal bearer token")
    provided_token = authorization[len(prefix) :]
    if not secrets.compare_digest(provided_token, expected_token):
        raise HTTPException(status_code=401, detail="invalid portal bearer token")
