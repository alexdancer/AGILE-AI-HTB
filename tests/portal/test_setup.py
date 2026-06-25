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

def test_setup_overview_and_budget_settings_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        setup = client.get("/setup", headers=_portal_headers())
        assert setup.status_code == 200
        assert "First-run setup" in setup.text
        assert "next missing action" in setup.text
        assert "Open Control plane model" in setup.text
        assert "Token budget" in setup.text

        saved = client.post(
            "/settings/budget",
            headers={**_portal_headers(), "Accept": "text/html"},
            data={"daily_cap_tokens": "999000", "session_cap_tokens": "111000"},
            follow_redirects=False,
        )
        assert saved.status_code == 303
        assert saved.headers["location"] == "/setup"
        page = client.get("/settings/budget", headers=_portal_headers())

    assert page.status_code == 200
    assert 'value="999000"' in page.text
    assert 'value="111000"' in page.text
    assert db.get_token_budget_settings(tmp_path / "harness.db") == {
        "confirmed": True,
        "daily_cap_tokens": 999000,
        "session_cap_tokens": 111000,
    }

def test_saved_budget_gates_launch_and_is_carried_to_session(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        _connect_project(database_path, tmp_path / "connected-project")
        db.set_token_budget_settings(database_path, daily_cap_tokens=1000, session_cap_tokens=700)
        db.update_worker_adapter(
            database_path,
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.1-codex"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(database_path, "codex", verified=True, evidence={"ok": True})
        project_metadata = _project_metadata(database_path, tmp_path / "connected-project")
        blocked = db.create_task(
            database_path,
            description="Too large for saved budget",
            status="Estimated",
            estimate_tokens=1200,
            recommended_model="gpt-5.1-codex",
            metadata=project_metadata,
        )
        ok = db.create_task(
            database_path,
            description="Within saved budget",
            status="Estimated",
            estimate_tokens=500,
            recommended_model="gpt-5.1-codex",
            metadata=project_metadata,
        )
        blocked_response = client.post(
            f"/tasks/{blocked['id']}/launch",
            headers=_portal_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.1-codex"},
        )

        def fake_runner(plan):
            return {"returncode": 0, "stdout": "", "stderr": ""}

        getattr(client.app, "state").task_launch_runner = fake_runner
        launched = client.post(
            f"/tasks/{ok['id']}/launch",
            headers=_portal_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.1-codex"},
        )

    assert blocked_response.status_code == 409
    assert "Task estimate exceeds remaining launch budget." in str(blocked_response.json())
    assert launched.status_code == 200
    session = launched.json()["session"]
    assert session["guardrail_overrides"]["budget"]["daily_cap_tokens"] == 1000
    assert session["guardrail_overrides"]["budget"]["session_cap_tokens"] == 700

