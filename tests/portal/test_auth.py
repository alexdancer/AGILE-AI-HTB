import os
from pathlib import Path

from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.operator_config import CONTROL_API_KEY_PLACEHOLDER, load_operator_config
from agile_ai_htb.project_context import project_task_metadata
from agile_ai_htb.settings import Settings

ROOT = Path(__file__).resolve().parents[2]
PORTAL_TOKEN = "test-portal-token"


class FakeControlPlaneLLM:
    def __init__(self, *, exc: Exception | None = None):
        self.exc = exc
        self.requests = []

    async def acompletion(self, request):
        self.requests.append(request)
        if self.exc:
            raise self.exc
        return {
            "choices": [{"message": {"content": "AGILE_AI_HTB_CONTROL_PLANE_OK"}}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10},
            "api_key": "sk_should_not_render",
        }


def _client(tmp_path):
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    return TestClient(create_app(settings))


def _client_with_control_plane_llm(tmp_path, llm, *, control_plane_model="anthropic/claude-sonnet-4-20250514"):
    settings = Settings(
        database_path=tmp_path / "harness.db",
        guardrails_path=ROOT / "guardrails.yaml",
        control_plane_model=control_plane_model,
        control_plane_api_key_env="TEST_CONTROL_PLANE_KEY",
    )
    app = create_app(settings)
    app.state.llm_client = llm
    return TestClient(app)


def _portal_headers():
    return {"Authorization": f"Bearer {PORTAL_TOKEN}"}


def _connect_project(database_path: Path, root: Path) -> dict:
    root.mkdir(exist_ok=True)
    return db.upsert_connected_project(
        database_path,
        name=root.name,
        root_path=str(root.resolve()),
        profile={"name": root.name, "root_path": str(root.resolve()), "test_command": "pytest"},
        capability={"state": "launch_ready", "can_launch": True},
    )


def _project_metadata(database_path: Path, root: Path) -> dict:
    return project_task_metadata(_connect_project(database_path, root))

def test_portal_routes_require_operator_bearer_token(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            json={"task_description": "Secured portal", "model": "claude-haiku"},
        ).json()

        for path in ["/dashboard", "/board", f"/sessions/{started['session_id']}"]:
            assert client.get(path).status_code == 401
            assert client.get(path, headers={"Authorization": "Bearer wrong"}).status_code == 401
            assert client.get(path, headers=_portal_headers()).status_code == 200

def test_portal_login_sets_signed_http_only_cookie_and_logout_clears_it(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN}, follow_redirects=False)

        assert login.status_code == 303
        assert login.headers["location"] == "/projects"
        cookie = login.headers["set-cookie"]
        assert "agile_ai_htb_portal=" in cookie
        assert "HttpOnly" in cookie
        assert "SameSite=lax" in cookie
        assert "Max-Age=43200" in cookie
        assert "Secure" not in cookie

        assert client.get("/dashboard").status_code == 200

        logout = client.post("/logout", follow_redirects=False)
        assert logout.status_code == 303
        assert logout.headers["location"] == "/login"
        assert "agile_ai_htb_portal=\"\"" in logout.headers["set-cookie"]
        assert client.get("/dashboard").status_code == 401

def test_portal_login_redirects_to_most_recent_project(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    db.init_db(tmp_path / "harness.db")
    db.upsert_connected_project(
        tmp_path / "harness.db",
        name="first-project",
        root_path=str(tmp_path / "first-project"),
        profile={},
        capability={},
    )
    recent = db.upsert_connected_project(
        tmp_path / "harness.db",
        name="second-project",
        root_path=str(tmp_path / "second-project"),
        profile={},
        capability={},
    )

    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN}, follow_redirects=False)

    assert login.status_code == 303
    assert login.headers["location"] == f"/projects/{recent['id']}"

def test_portal_rejects_tampered_or_expired_login_cookie(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN})
        assert login.status_code == 200
        signed_cookie = client.cookies.get("agile_ai_htb_portal")
        assert signed_cookie is not None

        client.cookies.set("agile_ai_htb_portal", signed_cookie + "tampered")
        assert client.get("/dashboard").status_code == 401

        from agile_ai_htb.auth import sign_portal_cookie

        client.cookies.set("agile_ai_htb_portal", sign_portal_cookie(PORTAL_TOKEN, max_age_seconds=-1))
        assert client.get("/dashboard").status_code == 401

def test_portal_login_rejects_wrong_token(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.post("/login", data={"token": "wrong"})

    assert response.status_code == 401

