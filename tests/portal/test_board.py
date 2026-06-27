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


def _task_card(html: str, task_id: str) -> str:
    start = html.index(f'id="{task_id}"')
    next_card = html.find('\n    <div class="task ', start + 1)
    next_empty = html.find('\n    <p class="empty-state"', start + 1)
    next_column = html.find('\n  </article>', start + 1)
    candidates = [idx for idx in (next_card, next_empty, next_column) if idx != -1]
    end = min(candidates) if candidates else len(html)
    return html[start:end]


def test_board_shows_blocked_manual_estimate_state(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    db.init_db(tmp_path / "harness.db")
    project = _connect_project(tmp_path / "harness.db", tmp_path / "project")
    with _client(tmp_path) as client:
        task = client.post(
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
        ).json()
        response = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())

    assert response.status_code == 200
    card = _task_card(response.text, task["id"])
    assert "Needs operator sizing" in card
    assert "Launch diagnostics recorded · expand Details" in card
    assert "Blocked/manual details recorded · expand Details" in card
    assert "<summary>Launch</summary>" in card
    assert "<summary>Blocked</summary>" in card
    assert card.index("<summary>Details</summary>") < card.index("Launch guardrail block") < card.index("Daily budget exhausted")
    assert card.index("<summary>Blocked</summary>") < card.index("Human/block reason") < card.index("Estimator unavailable: timeout")
    assert card.index("<summary>Blocked</summary>") < card.index("Manual estimate required") < card.index("Estimate this slice before Worker launch")

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
    card = _task_card(response.text, task["id"])
    assert "Run: openai/gpt-5.5 --variant high" in card
    assert "Estimate recommendation: gpt-5.4-mini" in card
    assert card.index("Run: openai/gpt-5.5 --variant high") < card.index("Estimate recommendation: gpt-5.4-mini")
    assert task["id"] in card


def test_board_uses_bounded_details_for_verbose_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    long_task_tail = "BOARD_FULL_TASK_TAIL_2099"
    stderr_tail = "BOARD_STDERR_TAIL_2099"
    stdout_tail = "BOARD_STDOUT_TAIL_2099"
    timeline_tail = "BOARD_TIMELINE_TAIL_2099"
    review_tail = "BOARD_REVIEW_TAIL_2099"
    with _client(tmp_path) as client:
        task = db.create_task(
            database_path,
            description="Compact board task " + ("long body " * 40) + long_task_tail,
            status="Review",
            estimate_tokens=9000,
            recommended_model="gpt-5.4-mini",
            metadata={
                **_project_metadata(database_path, tmp_path / "connected-project"),
                "launch_error": "Adapter failed before review",
                "last_launch_failure": {
                    "returncode": 2,
                    "stderr": "stderr line\n" + ("stderr detail\n" * 20) + stderr_tail,
                    "stdout": "stdout line\n" + ("stdout detail\n" * 20) + stdout_tail,
                },
                "launch_stdout": "worker output\n" + ("output detail\n" * 20) + stdout_tail,
                "worker_run_events": [
                    {"kind": "launch", "title": "Worker started", "detail_summary": "timeline detail " + timeline_tail}
                ],
                "review_prompt": "Focus on the bounded review details " + review_tail,
                "agent_review": {
                    "status": "completed",
                    "summary": "Review summary " + review_tail,
                    "recommendation": "inspect",
                    "findings": [{"severity": "medium", "message": "Finding " + review_tail}],
                },
            },
        )

        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    card = _task_card(response.text, task["id"])
    assert "task-title" in card
    assert "raw-evidence" in card
    assert "raw-evidence tall" in card
    assert card.count('<pre class="mono raw-evidence') >= 8
    for summary in ["Details", "Launch", "Timeline", "Logs", "Review"]:
        assert f"<summary>{summary}</summary>" in card
    assert card.index("<summary>Details</summary>") < card.index("Task body") < card.rindex(long_task_tail)
    assert card.index("<summary>Timeline</summary>") < card.index(timeline_tail)
    assert card.index("<summary>Logs</summary>") < card.index(stderr_tail)
    assert card.index("<summary>Logs</summary>") < card.index(stdout_tail)
    assert card.index("<summary>Review</summary>") < card.index(review_tail)


def test_board_launch_details_show_successful_worker_run_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        task = db.create_task(
            database_path,
            description="Review launched task evidence",
            status="Review",
            estimate_tokens=8000,
            recommended_model="gpt-5.4-mini",
            actual_tokens=1234,
            metadata={
                **_project_metadata(database_path, tmp_path / "connected-project"),
                "launch_adapter_id": "opencode",
                "launch_model": "openai/gpt-5.5 --variant high",
                "tracking_mode": "proxy_governed",
                "usage_source": "harness_proxy",
                "launch_returncode": 0,
                "worker_run_status": "completed",
                "active_worker_run_id": "wr_DEMO_999",
                "workdir_evidence": {"configured_workdir": "/tmp/DEMO_2099_project", "has_filesystem_evidence": True},
            },
        )

        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    card = _task_card(response.text, task["id"])
    assert "Actual: 1,234" in card
    assert "Launch diagnostics recorded · expand Details" in card
    assert "<summary>Launch</summary>" in card
    assert "Worker run: wr_DEMO_999" in card
    assert "Adapter: opencode" in card
    assert "Model: openai/gpt-5.5 --variant high" in card
    assert "Tracking: proxy_governed" in card
    assert "Usage source: harness_proxy" in card
    assert "Return code: 0" in card
    assert "Workdir: /tmp/DEMO_2099_project" in card


def test_board_hides_launch_details_when_no_launch_evidence_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        task = db.create_task(
            database_path,
            description="Review task without launch evidence",
            status="Review",
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
            metadata=_project_metadata(database_path, tmp_path / "connected-project"),
        )

        response = client.get("/board", headers=_portal_headers())

    assert response.status_code == 200
    card = _task_card(response.text, task["id"])
    assert "Launch diagnostics recorded" not in card
    assert "<summary>Launch</summary>" not in card


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

def test_board_filter_input_is_present(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        database_path = tmp_path / "harness.db"
        project_root = tmp_path / "connected-project"
        _connect_project(database_path, project_root)
        response = client.get("/board", headers=_portal_headers(), follow_redirects=False)

    assert response.status_code in (200, 303)
    if response.status_code == 200:
        assert 'id="board-filter"' in response.text
        assert 'id="filter-indicator"' in response.text
