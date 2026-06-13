from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request

PORTAL_COOKIE_NAME = "agile_ai_htb_portal"
PORTAL_COOKIE_MAX_AGE_SECONDS = 12 * 60 * 60


def require_portal_auth(request: Request) -> None:
    token_env = request.app.state.settings.portal_token_env
    expected_token = os.getenv(token_env, "")
    if not expected_token:
        raise HTTPException(status_code=401, detail="missing portal token configuration")

    authorization = request.headers.get("authorization", "")
    prefix = "Bearer "
    if authorization.startswith(prefix):
        provided_token = authorization[len(prefix) :]
        if secrets.compare_digest(provided_token, expected_token):
            return
        raise HTTPException(status_code=401, detail="invalid portal bearer token")

    cookie_value = request.cookies.get(PORTAL_COOKIE_NAME)
    if cookie_value and verify_portal_cookie(cookie_value, expected_token):
        return

    raise HTTPException(status_code=401, detail="missing portal authentication")


def sign_portal_cookie(secret: str, *, max_age_seconds: int = PORTAL_COOKIE_MAX_AGE_SECONDS) -> str:
    expires_at = int((datetime.now(UTC) + timedelta(seconds=max_age_seconds)).timestamp())
    payload = _b64_json({"expires_at": expires_at})
    signature = hmac.new(secret.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def verify_portal_cookie(cookie_value: str, secret: str) -> bool:
    try:
        payload, signature = cookie_value.rsplit(".", 1)
    except ValueError:
        return False

    expected = hmac.new(secret.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return False

    try:
        data = _unb64_json(payload)
        expires_at = int(data["expires_at"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False

    return expires_at > int(datetime.now(UTC).timestamp())


def _b64_json(data: dict[str, Any]) -> str:
    raw = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64_json(value: str) -> dict[str, Any]:
    padded = value + "=" * (-len(value) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    decoded = json.loads(raw)
    if not isinstance(decoded, dict):
        raise ValueError("cookie payload must be object")
    return decoded
