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

def test_sessions_index_renders_mockup_style_session_table(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            json={"task_description": "Review live portal", "model": "claude-haiku"},
        ).json()
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=started["session_id"],
            model="claude-haiku",
            prompt_tokens=80,
            completion_tokens=20,
            cost=0.01,
            raw_usage={"total_tokens": 100},
        )
        response = client.get("/sessions", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "All sessions" in html
    assert "summary before raw report" in html
    assert "table-wrap" in html
    assert "Review live portal" in html
    assert "100" in html
    assert "0 runs" in html
    assert "0 events" in html
    assert "zone:" in html

def test_session_report_renders_totals_alarm_checkpoint_without_internal_artifact_link(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            json={"task_description": "Audit session", "model": "claude-haiku"},
        ).json()
        session_id = started["session_id"]
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=session_id,
            model="claude-haiku",
            prompt_tokens=300,
            completion_tokens=200,
            cost=0.02,
            raw_usage={"total_tokens": 500},
        )
        db.record_guardrail_snapshot(
            tmp_path / "harness.db",
            session_id=session_id,
            zone="yellow",
            decision={"blocked_tools": ["web_search"], "max_tokens": 2048},
        )
        db.record_alarm(
            tmp_path / "harness.db",
            session_id=session_id,
            alarm={
                "id": "alarm-report-1",
                "type": "CHECKPOINT_FAIL",
                "severity": "MEDIUM",
                "context": {"checkpoint_name": "budget_health"},
                "recommended_action": "Human review required.",
            },
        )
        db.record_checkpoint_result(
            tmp_path / "harness.db",
            session_id=session_id,
            checkpoint={"name": "budget_health", "passed": False, "details": {"reason": "over budget"}},
        )
        task = db.create_task(
            tmp_path / "harness.db",
            description="Audit session",
            status="Running",
            session_id=session_id,
        )
        worker_run = db.create_worker_run(
            tmp_path / "harness.db",
            task_id=task["id"],
            session_id=session_id,
            adapter_id="opencode",
            model="claude-haiku",
            tracking_mode="proxy_governed",
            command_plan={"command": ["opencode"], "env": {}, "metadata": {}},
            metadata={
                "repo_context_brief": {
                    "documents": [{"path": "AGENTS.md", "excerpt": "Use pytest."}],
                    "manifests": ["pyproject.toml"],
                    "text": "Project root: /tmp/demo\n\nRepo instructions/docs:\n- AGENTS.md:\nUse pytest.",
                }
            },
        )
        db.record_worker_run_event(
            tmp_path / "harness.db",
            worker_run_id=worker_run["id"],
            session_id=session_id,
            task_id=task["id"],
            kind="guardrail",
            title="Worker Run failed",
            level="error",
            detail={
                "api_key": "***",
                "documents": ["AGENTS.md"],
                "error_type": "workdir_mismatch",
                "returncode": 124,
                "retryable": True,
            },
        )

        response = client.get(f"/sessions/{session_id}", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Audit session" in html
    assert "500" in html
    assert "yellow" in html
    assert "CHECKPOINT_FAIL" in html
    assert "budget_health" in html
    assert "Requires review" in html
    assert "Status / result" in html
    assert "review needed" in html
    assert "Worker launch" in html
    assert "opencode" in html
    assert "proxy_governed" in html
    assert "target: opencode" in html
    assert "Usage / guardrails" in html
    assert "Evidence coverage" in html
    assert "1 runs" in html
    assert "1 timeline events" in html
    assert "1 errors" in html
    assert "missing project evidence" in html
    assert "raw timeline evidence" in html
    assert "raw prompt context evidence" in html
    assert f"/session/{session_id}/artifact" not in html
    assert "session_key_hash" not in html
    assert "guardrail_overrides" not in html
    assert "Worker Run timeline" in html
    assert "Worker Run failed" in html
    assert "error_type=workdir_mismatch" in html
    assert "returncode=124" in html
    assert "retryable=True" in html
    assert "control_plane" in html
    assert "Repo Context Brief" in html
    assert "AGENTS.md" in html
    assert "pyproject.toml" in html
    assert "sk_secret_123" not in html

def test_session_report_missing_session_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/sessions/missing", headers=_portal_headers())

    assert response.status_code == 404

