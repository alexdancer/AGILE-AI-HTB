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

def test_board_shows_blocked_manual_estimate_state(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    db.init_db(tmp_path / "harness.db")
    project = _connect_project(tmp_path / "harness.db", tmp_path / "project")
    with _client(tmp_path) as client:
        client.post(
            "/tasks",
            json={
                "description": "Needs operator sizing",
                "metadata": {
                    **project_task_metadata(project),
                    "launch_blocked_reason": "Daily budget exhausted",
                    "launch_retryable": False,
                    "blocked_reason": "Estimator unavailable: timeout",
                    "requires_manual_estimate": True,
                },
            },
        )
        response = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())

    assert response.status_code == 200
    assert "Needs operator sizing" in response.text
    assert "Launch guardrail block:" in response.text
    assert "Daily budget exhausted" in response.text
    assert "Estimator unavailable: timeout" in response.text
    assert "Human/block reason:" in response.text
    assert "Manual estimate required" in response.text
    assert "Estimate this slice before Worker launch" in response.text

def test_project_board_filters_tasks_and_global_board_redirects_to_recent_project(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    first = _connect_project(database_path, tmp_path / "first")
    second = _connect_project(database_path, tmp_path / "second")
    db.create_task(
        database_path,
        description="First project task",
        status="Blocked",
        metadata={**project_task_metadata(first), "blocked_reason": "manual"},
    )
    db.create_task(
        database_path,
        description="Second project task",
        status="Blocked",
        metadata={**project_task_metadata(second), "blocked_reason": "manual"},
    )
    db.create_task(database_path, description="Legacy global task", status="Blocked")

    with _client(tmp_path) as client:
        first_board = client.get(f"/projects/{first['id']}/board", headers=_portal_headers())
        global_board = client.get("/board", headers=_portal_headers(), follow_redirects=False)

    assert first_board.status_code == 200
    assert "First project task" in first_board.text
    assert "Second project task" not in first_board.text
    assert "Legacy global task" not in first_board.text
    assert global_board.status_code == 303
    assert global_board.headers["location"] == f"/projects/{second['id']}/board"

def test_global_board_redirects_to_projects_when_none_connected(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    with _client(tmp_path) as client:
        response = client.get("/board", headers=_portal_headers(), follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/projects"

def test_board_renders_columns_and_task_cards(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        created = client.post(
            "/tasks",
            json={
                "description": "Add streaming proxy tests",
                "status": "Estimated",
                "estimate_tokens": 25000,
                "recommended_model": "claude-sonnet",
                "actual_tokens": 12000,
                "metadata": _project_metadata(tmp_path / "harness.db", tmp_path / "connected-project"),
            },
        ).json()
        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    for column in ["Estimated", "Running", "Review", "Done", "Blocked"]:
        assert column in html
    assert "Backlog" not in html
    assert "Other" not in html
    assert "max-width: none" in html
    assert "repeat(6, minmax(260px, 1fr))" in html
    assert "task-title" in html
    assert "task-meta" in html
    assert '<details class="task-details">' in html
    assert "Details" in html
    assert "No Running tasks. Launched Worker slices appear here" in html
    assert "No Review tasks. Completed Worker runs" in html
    assert "No Done tasks. Accepted Review work lands here" in html
    assert "No Blocked tasks. Guardrail blocks" in html
    assert "Add streaming proxy tests" in html
    assert "25,000" in html
    assert "Model: claude-sonnet" in html
    assert "12,000" in html
    assert "Launch task" in html
    assert "adapter_id" in html
    assert created["id"] in html

def test_board_shows_launched_model_before_recommendation(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        task = db.create_task(
            database_path,
            description="Run with operator selected model",
            status="Running",
            estimate_tokens=25000,
            recommended_model="gpt-5.4-mini",
            metadata={
                **_project_metadata(database_path, tmp_path / "connected-project"),
                "launch_model": "openai/gpt-5.5 --variant high",
            },
        )

        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert "Run: openai/gpt-5.5 --variant high" in html
    assert "Recommended: gpt-5.4-mini" in html
    assert task["id"] in html

def test_board_renders_unexpected_statuses_as_blocked(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        client.post(
            "/tasks",
            json={
                "description": "Odd status task",
                "status": "Legacy Backlog",
                "metadata": _project_metadata(tmp_path / "harness.db", tmp_path / "connected-project"),
            },
        )
        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    assert "Blocked" in response.text
    assert "Other" not in response.text
    assert "Odd status task" in response.text
    assert "Unsupported task status: Legacy Backlog" in response.text

def test_board_review_card_shows_disposition_actions_prompt_and_agent_review(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        session = db.create_session(
            database_path,
            task_description="Review UI task",
            model="gpt-5.1-codex",
            session_key_hash="u" * 64,
            guardrail_overrides={},
            status="completed",
        )
        task = db.create_task(
            database_path,
            description="Review UI task",
            status="Review",
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
            session_id=session["id"],
            metadata={
                **_project_metadata(database_path, tmp_path / "connected-project"),
                "review_prompt": "DEMO focus note 2099",
                "launch_stdout": "DEMO worker stdout 2099",
                "agent_review": {
                    "status": "completed",
                    "summary": "DEMO agent review summary 2099",
                    "recommendation": "approve",
                    "findings": [{"severity": "low", "message": "DEMO finding 2099"}],
                },
            },
        )
        response = client.get("/board", headers=_portal_headers())
        validation = client.post(
            f"/tasks/{task['id']}/review",
            headers={**_portal_headers(), "Accept": "text/html"},
            data={"action": "block", "blocked_reason": ""},
            follow_redirects=False,
        )

    assert response.status_code == 200
    assert validation.status_code == 303
    assert validation.headers["location"].startswith(f"/projects/{task['metadata']['connected_project_id']}/board?error=")
    html = response.text
    assert f'action="/tasks/{task["id"]}/review"' in html
    assert "Agent Review" in html
    assert "Mark Done" in html
    assert "Block" in html
    assert "Review prompt / focus" in html
    assert "DEMO focus note 2099" in html
    assert "DEMO agent review summary 2099" in html
    assert "DEMO finding 2099" in html
    assert f"/sessions/{session['id']}" in html

def test_board_review_card_hides_actions_without_completed_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        task = db.create_task(
            database_path,
            description="Review task without completed evidence",
            status="Review",
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
            metadata=_project_metadata(database_path, tmp_path / "connected-project"),
        )
        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    card = response.text.split(f'id="{task["id"]}"', 1)[1].split('</div>', 1)[0]
    assert "Review actions require completed Worker Run evidence." in card
    assert f'action="/tasks/{task["id"]}/review"' not in card
    assert "Mark Done" not in card

def test_project_board_shows_context_indicator(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project_root = tmp_path / "connected-project"
        project = _connect_project(database_path, project_root)
        response = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())

    assert response.status_code == 200
    html = response.text
    assert f"Estimating with project context: {project['name']}" in html


def test_board_redirects_when_no_project(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/board", headers=_portal_headers(), follow_redirects=False)

    assert response.status_code == 303
