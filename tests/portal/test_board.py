from urllib.parse import unquote

from foreman_ai_hq import db
from foreman_ai_hq.board_automation import list_eligible_estimated_tasks
from foreman_ai_hq.project_context import project_task_metadata
from tests.portal.helpers import PORTAL_TOKEN, _client, _connect_project, _portal_headers, _project_metadata


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
    assert "repeat(6, minmax(340px, 1fr))" in html
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
    assert "Estimated Worker model: gpt-5.4-mini" in card
    assert f'action="/tasks/{task["id"]}/refresh"' in card
    assert "Refresh status" in card
    assert card.index("Run: openai/gpt-5.5 --variant high") < card.index("Estimated Worker model: gpt-5.4-mini")
    assert task["id"] in card


def test_board_uses_bounded_details_for_verbose_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    long_task_tail = "BOARD_FULL_TASK_TAIL_2099"
    stderr_tail = "BOARD_STDERR_TAIL_2099"
    stdout_tail = "BOARD_STDOUT_TAIL_2099"
    timeline_tail = "BOARD_TIMELINE_TAIL_2099"
    review_prompt_tail = "BOARD_REVIEW_PROMPT_TAIL_2099"
    review_summary_tail = "BOARD_REVIEW_SUMMARY_TAIL_2099"
    review_finding_tail = "BOARD_REVIEW_FINDING_TAIL_2099"
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
                "review_prompt": "Focus on the bounded review details " + review_prompt_tail,
                "agent_review": {
                    "status": "completed",
                    "summary": "Review summary " + review_summary_tail,
                    "recommendation": "inspect",
                    "findings": [{"severity": "medium", "message": "Finding " + review_finding_tail}],
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
    assert card.index("<summary>Review</summary>") < card.index(review_prompt_tail)
    assert card.index("Agent Review") < card.index(review_summary_tail)
    assert card.index("Agent Review") < card.index(review_finding_tail)


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
            recommended_model="5.4",
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
            model="5.4",
            session_key_hash="u" * 64,
            guardrail_overrides={},
            status="completed",
        )
        task = db.create_task(
            database_path,
            description="Review UI task",
            status="Review",
            estimate_tokens=8000,
            recommended_model="5.4",
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
            recommended_model="5.4",
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


def test_mark_done_keeps_task_visible_until_archived(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "connected-project")
        session = db.create_session(
            database_path,
            task_description="Accepted review task",
            model="5.4",
            session_key_hash="a" * 64,
            guardrail_overrides={},
            status="completed",
        )
        task = db.create_task(
            database_path,
            description="Accepted review task",
            status="Review",
            estimate_tokens=8000,
            recommended_model="5.4",
            actual_tokens=4200,
            session_id=session["id"],
            metadata=project_task_metadata(project),
        )

        response = client.post(
            f"/tasks/{task['id']}/review",
            headers={**_portal_headers(), "Accept": "text/html"},
            data={"action": "mark_done", "project_id": project["id"]},
            follow_redirects=False,
        )
        board = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())

    updated = db.get_task(database_path, task["id"])
    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{project['id']}/board"
    assert updated["status"] == "Done"
    assert "archived_at" not in updated["metadata"]
    assert board.status_code == 200
    card = _task_card(board.text, task["id"])
    assert "Accepted review task" in card
    assert "Archive" in card


def test_archive_done_task_hides_from_board_and_preserves_history_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "connected-project")
        session = db.create_session(
            database_path,
            task_description="Archived done task",
            model="5.4",
            session_key_hash="b" * 64,
            guardrail_overrides={},
            status="completed",
        )
        task = db.create_task(
            database_path,
            description="Archived done task",
            status="Done",
            estimate_tokens=9000,
            recommended_model="5.4",
            actual_tokens=4500,
            session_id=session["id"],
            metadata={**project_task_metadata(project), "active_worker_run_id": "wr_DEMO_999"},
        )

        archive_response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}/archive",
            headers=_portal_headers(),
            follow_redirects=False,
        )
        board = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())
        history = client.get(f"/projects/{project['id']}/task-history", headers=_portal_headers())

    archived = db.get_task(database_path, task["id"])
    assert archive_response.status_code == 303
    assert archive_response.headers["location"] == f"/projects/{project['id']}/board"
    assert archived["status"] == "Done"
    assert archived["actual_tokens"] == 4500
    assert archived["session_id"] == session["id"]
    assert archived["metadata"]["archived_at"]
    assert board.status_code == 200
    assert "Archived done task" not in board.text
    assert "History 1 · Archived 1" in board.text
    assert history.status_code == 200
    assert "Archived done task" in history.text
    assert "Archived" in history.text
    assert "Actual: 4,500" in history.text
    assert f"/sessions/{session['id']}" in history.text
    assert "Worker Run: wr_DEMO_999" in history.text
    assert "Unarchive" in history.text


def test_react_archive_actions_return_stable_json_and_preserve_project_binding(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "react-archive-project")
        other = _connect_project(database_path, tmp_path / "react-archive-other")
        individual = db.create_task(
            database_path,
            description="Archive one DEMO task",
            status="Done",
            metadata=project_task_metadata(project),
        )
        bulk = db.create_task(
            database_path,
            description="Archive remaining DEMO task",
            status="Done",
            metadata=project_task_metadata(project),
        )

        archived = client.post(
            f"/projects/{project['id']}/tasks/{individual['id']}/archive",
            headers={**_portal_headers(), "accept": "application/json"},
        )
        wrong_project = client.post(
            f"/projects/{other['id']}/tasks/{bulk['id']}/archive",
            headers={**_portal_headers(), "accept": "application/json"},
        )
        archived_all = client.post(
            f"/projects/{project['id']}/tasks/archive-done",
            headers={**_portal_headers(), "accept": "application/json"},
        )

    assert archived.status_code == 200
    assert archived.json() == {
        "ok": True,
        "error": None,
        "setup_href": None,
        "next_href": None,
        "task": {"id": individual["id"], "status": "Done"},
    }
    assert wrong_project.status_code == 404
    assert wrong_project.json() == {
        "ok": False,
        "error": "task not found for selected project",
        "setup_href": None,
        "next_href": None,
        "task": None,
    }
    assert archived_all.status_code == 200
    assert archived_all.json() == {
        "ok": True,
        "error": None,
        "setup_href": None,
        "next_href": None,
        "task": None,
    }
    assert db.get_task(database_path, bulk["id"])["metadata"]["archived_at"]


def test_archive_blocked_task_hides_from_board_and_preserves_history_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "connected-project")
        session = db.create_session(
            database_path,
            task_description="Archived blocked task",
            model="5.4",
            session_key_hash="c" * 64,
            guardrail_overrides={},
            status="completed",
        )
        task = db.create_task(
            database_path,
            description="Archived blocked task",
            status="Blocked",
            estimate_tokens=7000,
            recommended_model="5.4",
            actual_tokens=2100,
            session_id=session["id"],
            metadata={
                **project_task_metadata(project),
                "blocked_reason": "Needs product decision",
                "requires_manual_estimate": True,
                "active_worker_run_id": "wr_DEMO_999_BLOCKED",
            },
        )

        archive_response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}/archive",
            headers=_portal_headers(),
            follow_redirects=False,
        )
        board = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())
        history = client.get(f"/projects/{project['id']}/task-history?filter=archived", headers=_portal_headers())

    archived = db.get_task(database_path, task["id"])
    assert archive_response.status_code == 303
    assert archive_response.headers["location"] == f"/projects/{project['id']}/board"
    assert archived["status"] == "Blocked"
    assert archived["actual_tokens"] == 2100
    assert archived["session_id"] == session["id"]
    assert archived["metadata"]["blocked_reason"] == "Needs product decision"
    assert archived["metadata"]["requires_manual_estimate"] is True
    assert archived["metadata"]["active_worker_run_id"] == "wr_DEMO_999_BLOCKED"
    assert archived["metadata"]["archived_at"]
    assert board.status_code == 200
    assert "Archived blocked task" not in board.text
    assert "History 1 · Archived 1" in board.text
    assert history.status_code == 200
    assert "Archived blocked task" in history.text
    assert "Blocked" in history.text
    assert "Archived" in history.text
    assert "Actual: 2,100" in history.text
    assert f"/sessions/{session['id']}" in history.text
    assert "Worker Run: wr_DEMO_999_BLOCKED" in history.text
    assert "Blocked: Needs product decision" in history.text
    assert "Manual estimate required" in history.text
    assert "Unarchive" in history.text


def test_dismiss_estimated_task_hides_from_board_and_preserves_history_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "connected-project")
        task = db.create_task(
            database_path,
            description="Dismiss estimated task",
            status="Estimated",
            estimate_tokens=9000,
            recommended_model="5.4",
            metadata={
                **project_task_metadata(project),
                "launch_adapter_id": "opencode",
                "launch_model": "5.4",
            },
        )

        initial_board = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())
        dismiss_response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}/archive",
            headers=_portal_headers(),
            follow_redirects=False,
        )
        dismissed_board = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())
        history = client.get(f"/projects/{project['id']}/task-history?filter=archived", headers=_portal_headers())
        dismissed = db.get_task(database_path, task["id"])
        eligible_after_dismiss = list_eligible_estimated_tasks(database_path, project["id"])
        unarchive_response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}/unarchive",
            headers=_portal_headers(),
            follow_redirects=False,
        )
        restored_board = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())
        restored = db.get_task(database_path, task["id"])
        eligible_after_restore = list_eligible_estimated_tasks(database_path, project["id"])

    assert initial_board.status_code == 200
    initial_card = _task_card(initial_board.text, task["id"])
    assert "Dismiss estimated task" in initial_card
    assert "Dismiss" in initial_card
    assert dismiss_response.status_code == 303
    assert dismiss_response.headers["location"] == f"/projects/{project['id']}/board"
    assert dismissed["status"] == "Estimated"
    assert dismissed["estimate_tokens"] == 9000
    assert dismissed["recommended_model"] == "5.4"
    assert dismissed["metadata"]["launch_adapter_id"] == "opencode"
    assert dismissed["metadata"]["archived_at"]
    assert eligible_after_dismiss == []
    assert dismissed_board.status_code == 200
    assert "Dismiss estimated task" not in dismissed_board.text
    assert "History 1 · Archived 1" in dismissed_board.text
    assert history.status_code == 200
    assert "Dismiss estimated task" in history.text
    assert "Estimated" in history.text
    assert "Archived" in history.text
    assert "Estimate: 9,000" in history.text
    assert "Model: 5.4" in history.text
    assert "Unarchive" in history.text
    assert unarchive_response.status_code == 303
    assert unarchive_response.headers["location"] == f"/projects/{project['id']}/task-history"
    assert restored["status"] == "Estimated"
    assert "archived_at" not in restored["metadata"]
    assert restored_board.status_code == 200
    restored_card = _task_card(restored_board.text, task["id"])
    assert "Dismiss estimated task" in restored_card
    assert "Dismiss" in restored_card
    assert [task["id"] for task in eligible_after_restore] == [task["id"]]


def test_archive_all_done_is_project_scoped_and_keeps_estimation_accuracy(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        first_project = _connect_project(database_path, tmp_path / "first-project")
        second_project = _connect_project(database_path, tmp_path / "second-project")
        first_done = db.create_task(
            database_path,
            description="First done task",
            status="Done",
            estimate_tokens=1000,
            actual_tokens=500,
            metadata=project_task_metadata(first_project),
        )
        second_done = db.create_task(
            database_path,
            description="Second done task",
            status="Done",
            estimate_tokens=2000,
            actual_tokens=4000,
            metadata=project_task_metadata(first_project),
        )
        first_estimated = db.create_task(
            database_path,
            description="First estimated task",
            status="Estimated",
            estimate_tokens=3000,
            recommended_model="5.4",
            metadata=project_task_metadata(first_project),
        )
        other_done = db.create_task(
            database_path,
            description="Other project done task",
            status="Done",
            estimate_tokens=1000,
            actual_tokens=1000,
            metadata=project_task_metadata(second_project),
        )

        response = client.post(
            f"/projects/{first_project['id']}/tasks/archive-done",
            headers=_portal_headers(),
            follow_redirects=False,
        )
        first_board = client.get(f"/projects/{first_project['id']}/board", headers=_portal_headers())
        other_board = client.get(f"/projects/{second_project['id']}/board", headers=_portal_headers())

    assert response.status_code == 303
    assert db.get_task(database_path, first_done["id"])["metadata"].get("archived_at")
    assert db.get_task(database_path, second_done["id"])["metadata"].get("archived_at")
    assert not db.get_task(database_path, first_estimated["id"])["metadata"].get("archived_at")
    assert not db.get_task(database_path, other_done["id"])["metadata"].get("archived_at")
    assert "First done task" not in first_board.text
    assert "Second done task" not in first_board.text
    assert "First estimated task" in first_board.text
    assert "Other project done task" in other_board.text
    assert db.estimation_accuracy(database_path)["completed_count"] == 3


def test_unarchive_restores_done_task_to_project_board(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "connected-project")
        task = db.create_task(
            database_path,
            description="Return archived task",
            status="Done",
            estimate_tokens=9000,
            actual_tokens=4500,
            metadata={**project_task_metadata(project), "archived_at": "2099-01-01T00:00:00+00:00"},
        )

        response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}/unarchive",
            headers=_portal_headers(),
            follow_redirects=False,
        )
        board = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())

    updated = db.get_task(database_path, task["id"])
    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{project['id']}/task-history"
    assert updated["status"] == "Done"
    assert "archived_at" not in updated["metadata"]
    assert board.status_code == 200
    assert "Return archived task" in board.text


def test_unarchive_restores_blocked_task_to_project_board(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "connected-project")
        task = db.create_task(
            database_path,
            description="Return blocked task",
            status="Blocked",
            estimate_tokens=9000,
            metadata={
                **project_task_metadata(project),
                "blocked_reason": "Needs operator",
                "archived_at": "2099-01-01T00:00:00+00:00",
            },
        )

        response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}/unarchive",
            headers=_portal_headers(),
            follow_redirects=False,
        )
        board = client.get(f"/projects/{project['id']}/board", headers=_portal_headers())

    updated = db.get_task(database_path, task["id"])
    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{project['id']}/task-history"
    assert updated["status"] == "Blocked"
    assert updated["metadata"]["blocked_reason"] == "Needs operator"
    assert "archived_at" not in updated["metadata"]
    assert board.status_code == 200
    card = _task_card(board.text, task["id"])
    assert "Return blocked task" in card
    assert "Archive" in card


def test_archive_rejects_active_non_archivable_tasks(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    project = _connect_project(database_path, tmp_path / "connected-project")
    task_ids = []
    for blocked_status in ["Running", "Review"]:
        task = db.create_task(
            database_path,
            description=f"{blocked_status} task cannot archive",
            status=blocked_status,
            estimate_tokens=9000,
            recommended_model="5.4",
            metadata=project_task_metadata(project),
        )
        task_ids.append(task["id"])

    with _client(tmp_path) as client:
        responses = [
            client.post(
                f"/projects/{project['id']}/tasks/{task_id}/archive",
                headers=_portal_headers(),
                follow_redirects=False,
            )
            for task_id in task_ids
        ]

    for response, task_id in zip(responses, task_ids):
        assert response.status_code == 303
        assert response.headers["location"].startswith(f"/projects/{project['id']}/board?error=")
        assert "Only Done, Blocked, or Estimated tasks can be archived or dismissed." in unquote(response.headers["location"])
        assert not db.get_task(database_path, task_id)["metadata"].get("archived_at")

