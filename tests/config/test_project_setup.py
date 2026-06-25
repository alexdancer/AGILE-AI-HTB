from pathlib import Path
import time

from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.settings import Settings

ROOT = Path(__file__).resolve().parents[2]
PORTAL_TOKEN = "test-portal-token"


def _client(tmp_path, *, local_runner_enabled=True):
    settings = Settings(
        database_path=tmp_path / "harness.db",
        guardrails_path=ROOT / "guardrails.yaml",
        local_runner_enabled=local_runner_enabled,
    )
    return TestClient(create_app(settings))


def _headers():
    return {"Authorization": f"Bearer {PORTAL_TOKEN}"}


def _wait_for_worker_run(db_path: Path, task_id: str, status: str | None = None):
    deadline = time.time() + 2
    while time.time() < deadline:
        runs = db.list_worker_runs(db_path, task_id=task_id)
        if runs and (status is None or runs[-1]["status"] == status):
            return runs[-1]
        time.sleep(0.01)
    raise AssertionError("worker run did not reach expected status")


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "portal-project"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "portal-demo"\ndependencies = ["fastapi"]\n')
    (root / "README.md").write_text("# Portal Demo\n")
    (root / "src").mkdir()
    return root


def test_project_setup_rejects_disabled_local_runner(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    root = _project_root(tmp_path)

    with _client(tmp_path, local_runner_enabled=False) as client:
        response = client.post(
            "/settings/project/connect",
            headers=_headers(),
            json={"root_path": str(root)},
        )

    assert response.status_code == 409
    assert "htb init" in response.json()["detail"]
    assert "htb serve" in response.json()["detail"]


def test_project_setup_api_connects_valid_path_and_returns_detected_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    root = _project_root(tmp_path)

    with _client(tmp_path) as client:
        response = client.post(
            "/settings/project/connect",
            headers=_headers(),
            json={"root_path": str(root)},
        )

    assert response.status_code == 200
    project = response.json()["project"]
    assert project["root_path"] == str(root.resolve())
    assert project["profile"]["test_command"] == "pytest"
    assert project["profile"]["language_hints"] == ["python"]
    assert project["capability"]["state"] == "analysis_ready"


def test_project_setup_api_rejects_invalid_path_with_clear_error(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    with _client(tmp_path) as client:
        response = client.post(
            "/settings/project/connect",
            headers=_headers(),
            json={"root_path": str(tmp_path / "missing")},
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "Local project path does not exist."


def test_project_settings_page_displays_profile_and_capability_state(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    root = _project_root(tmp_path)

    with _client(tmp_path) as client:
        client.post("/settings/project/connect", headers=_headers(), json={"root_path": str(root)})
        response = client.get("/settings/project", headers=_headers())

    assert response.status_code == 200
    html = response.text
    assert "Projects" in html
    assert "portal-project" in html
    assert str(root.resolve()) in html
    assert "Analysis-ready" in html
    assert "pytest" in html
    assert "fastapi" in html
    assert "README.md" in html


def test_projects_page_lists_connected_projects_and_open_form(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    root = _project_root(tmp_path)

    with _client(tmp_path) as client:
        empty = client.get("/projects", headers=_headers())
        client.post("/settings/project/connect", headers=_headers(), json={"root_path": str(root)})
        listed = client.get("/projects", headers=_headers())

    assert empty.status_code == 200
    assert "Open local repo" in empty.text
    assert "No projects" in empty.text
    assert "No projects yet." in empty.text
    assert "Switch project" not in empty.text
    assert listed.status_code == 200
    assert "portal-project" in listed.text
    assert str(root.resolve()) in listed.text
    assert 'action="/settings/project/connect?redirect=workspace"' in listed.text


def test_projects_open_form_redirects_to_project_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    root = _project_root(tmp_path)

    with _client(tmp_path) as client:
        response = client.post(
            "/settings/project/connect?redirect=workspace",
            headers={**_headers(), "accept": "text/html"},
            data={"root_path": str(root)},
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/projects/")


def test_project_workspace_displays_profile_capability_and_workflow_links(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    root = _project_root(tmp_path)

    with _client(tmp_path) as client:
        project = client.post("/settings/project/connect", headers=_headers(), json={"root_path": str(root)}).json()["project"]
        db.create_task(tmp_path / "harness.db", description="Running workspace task", status="Running", metadata={"connected_project_id": project["id"]})
        db.create_task(tmp_path / "harness.db", description="Review workspace task", status="Review", metadata={"connected_project_id": project["id"]})
        db.create_task(tmp_path / "harness.db", description="Blocked workspace task", status="Blocked", metadata={"connected_project_id": project["id"], "blocked_reason": "guardrail"})
        response = client.get(f"/projects/{project['id']}", headers=_headers())
        missing = client.get("/projects/not-a-project", headers=_headers())

    assert response.status_code == 200
    html = response.text
    assert "portal-project" in html
    assert str(root.resolve()) in html
    assert "launch ready" in html or "setup needed" in html
    assert "3 tasks" in html
    assert "0 estimated" in html
    assert "Worker setup" in html
    assert "Running work" in html
    assert "Review needed" in html
    assert "Blocked work" in html
    assert "Session evidence" in html
    assert "Analysis-ready" in html
    assert "pytest" in html
    assert "fastapi" in html
    assert "README.md" in html
    for href in [f'href="/projects/{project["id"]}/board"', 'href="/sessions"', 'href="/settings/workers"', 'href="/settings/project"']:
        assert href in html
    assert missing.status_code == 404


def test_sidebar_lists_projects_and_marks_active_project(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    first_root = _project_root(tmp_path)
    second_root = tmp_path / "second-project"
    second_root.mkdir()
    (second_root / "pyproject.toml").write_text('[project]\nname = "second-demo"\n')

    with _client(tmp_path) as client:
        first = client.post("/settings/project/connect", headers=_headers(), json={"root_path": str(first_root)}).json()["project"]
        second = client.post("/settings/project/connect", headers=_headers(), json={"root_path": str(second_root)}).json()["project"]
        db.create_task(
            tmp_path / "harness.db",
            description="project task",
            status="Estimated",
            metadata={"connected_project_id": first["id"]},
        )
        dashboard = client.get("/dashboard", headers=_headers())
        workspace = client.get(f"/projects/{first['id']}", headers=_headers())
        board = client.get(f"/projects/{first['id']}/board", headers=_headers())

    assert dashboard.status_code == 200
    assert f'href="/projects/{first["id"]}" class="project-item ' in dashboard.text
    assert f'href="/projects/{second["id"]}" class="project-item ' in dashboard.text
    assert f'href="/projects/{first["id"]}/board" class="project-board"' in dashboard.text
    assert "Task board" in dashboard.text
    assert "No tasks" in dashboard.text
    assert "empty-state" in dashboard.text
    assert "Switch project" not in dashboard.text
    assert "+ Open local repo" in dashboard.text
    assert '<div class="group">Planning</div>' not in dashboard.text
    assert str(first_root.resolve()) not in dashboard.text
    assert workspace.status_code == 200
    assert f'href="/projects/{first["id"]}" class="project-item active"' in workspace.text
    assert board.status_code == 200
    assert f'href="/projects/{first["id"]}" class="project-item active"' in board.text


def test_login_sidebar_does_not_expose_projects_before_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    root = _project_root(tmp_path)

    with _client(tmp_path) as client:
        client.post("/settings/project/connect", headers=_headers(), json={"root_path": str(root)})
        response = client.get("/login")

    assert response.status_code == 200
    assert "portal-project" not in response.text


def test_project_page_shows_read_only_proof_only_when_launch_ready(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    root = _project_root(tmp_path)

    with _client(tmp_path) as client:
        connected = client.post("/settings/project/connect", headers=_headers(), json={"root_path": str(root)}).json()["project"]
        analysis_only = client.get("/settings/project", headers=_headers())
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "opencode", verified=True, evidence={"ok": True})
        launch_ready = client.get("/settings/project", headers=_headers())

    assert connected["capability"]["state"] == "analysis_ready"
    assert "Run read-only proof" not in analysis_only.text
    assert "Run read-only proof" in launch_ready.text


def test_project_read_only_proof_route_launches_when_launch_ready(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    root = _project_root(tmp_path)
    runner_calls = []

    with _client(tmp_path) as client:
        client.app.state.local_runner_proof_runner = lambda plan: (
            runner_calls.append(plan)
            or db.record_token_turn(
                tmp_path / "harness.db",
                session_id=plan.metadata["session_id"],
                usage_kind="task_execution",
                model="opencode/gpt-5.1",
                prompt_tokens=10,
                completion_tokens=5,
                cost=0,
                raw_usage={"total_tokens": 15},
            )
            or {"returncode": 0, "stdout": "report", "stderr": ""}
        )
        project = client.post("/settings/project/connect", headers=_headers(), json={"root_path": str(root)}).json()["project"]
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "opencode",
            supported_models=["opencode/gpt-5.1"],
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "opencode", verified=True, evidence={"ok": True})
        response = client.post(f"/settings/project/{project['id']}/read-only-proof", headers=_headers())

    body = response.json()
    assert response.status_code == 200
    assert body["task"]["status"] == "Running"
    _wait_for_worker_run(tmp_path / "harness.db", body["task"]["id"], "completed")
    completed = db.get_task(tmp_path / "harness.db", body["task"]["id"])
    assert completed["status"] == "Review"
    assert completed["metadata"]["read_only_proof"] is True
    assert completed["metadata"]["session_report"]["test_command"] == "pytest"
    assert runner_calls[0].cwd == root.resolve()
