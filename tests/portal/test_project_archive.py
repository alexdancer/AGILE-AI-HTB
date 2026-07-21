from foreman_ai_hq import db
from foreman_ai_hq.project_context import project_task_metadata
from tests.portal.helpers import PORTAL_TOKEN, _client, _connect_project, _portal_headers


def test_projects_page_hides_archived_project_from_active_list_and_restores(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    active = _connect_project(database_path, tmp_path / "active-repo")
    archived = _connect_project(database_path, tmp_path / "archived-repo")
    db.archive_connected_project(database_path, archived["id"])

    with _client(tmp_path) as client:
        response = client.get("/api/projects", headers=_portal_headers())
        restored = client.post(
            f"/projects/{archived['id']}/restore",
            headers=_portal_headers(),
            follow_redirects=False,
        )

    assert response.status_code == 200
    payload = response.json()
    active_names = {p["name"] for p in payload["projects"]}
    archived_names = {p["name"] for p in payload["archived_projects"]}
    assert active["name"] in active_names
    assert archived["name"] not in active_names
    assert archived["name"] in archived_names
    assert restored.status_code == 303
    assert restored.headers["location"] == f"/projects/{archived['id']}"
    assert db.get_connected_project(database_path, archived["id"])["archived_at"] is None


def test_restore_missing_project_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)

    with _client(tmp_path) as client:
        response = client.post("/projects/missing-project-999/restore", headers=_portal_headers())

    assert response.status_code == 404


def test_sidebar_and_global_board_ignore_archived_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    active = _connect_project(database_path, tmp_path / "active-board-repo")
    archived = _connect_project(database_path, tmp_path / "archived-board-repo")
    db.archive_connected_project(database_path, archived["id"])

    with _client(tmp_path) as client:
        projects = client.get("/api/projects", headers=_portal_headers())
        board = client.get("/board", headers=_portal_headers(), follow_redirects=False)

    assert projects.status_code == 200
    payload = projects.json()
    active_names = {p["name"] for p in payload["projects"]}
    assert active["name"] in active_names
    assert archived["name"] not in active_names
    assert board.status_code == 303
    assert board.headers["location"] == f"/projects/{active['id']}"


def test_global_board_redirects_to_projects_when_only_archived_projects_exist(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    project = _connect_project(database_path, tmp_path / "only-archived-repo")
    db.archive_connected_project(database_path, project["id"])

    with _client(tmp_path) as client:
        board = client.get("/board", headers=_portal_headers(), follow_redirects=False)

    assert board.status_code == 303
    assert board.headers["location"] == "/projects"


def test_archive_project_rejects_running_work(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    project = _connect_project(database_path, tmp_path / "running-repo")
    db.create_task(
        database_path,
        description="Currently running",
        status="Running",
        metadata=project_task_metadata(project),
    )

    with _client(tmp_path) as client:
        response = client.post(
            f"/projects/{project['id']}/archive",
            headers=_portal_headers(),
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/settings/project?error=")
    assert db.get_connected_project(database_path, project["id"])["archived_at"] is None


def test_archive_project_rejects_active_worker_run_on_archived_task(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    project = _connect_project(database_path, tmp_path / "archived-task-running-repo")
    task = db.create_task(
        database_path,
        description="Archived task still has active run",
        status="Done",
        metadata=project_task_metadata(project),
    )
    db.archive_task(database_path, task["id"])
    session = db.create_session(
        database_path,
        task_description=task["description"],
        model="opencode/gpt-5.1",
        session_key_hash="hash-999",
        guardrail_overrides={},
    )
    db.create_worker_run(
        database_path,
        task_id=task["id"],
        session_id=session["id"],
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        tracking_mode="proxy_governed",
        command_plan={"command": ["opencode", "run"]},
        status="running",
    )

    with _client(tmp_path) as client:
        response = client.post(
            f"/projects/{project['id']}/archive",
            headers=_portal_headers(),
            follow_redirects=False,
        )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/settings/project?error=")
    assert db.get_connected_project(database_path, project["id"])["archived_at"] is None


def test_archived_project_workspace_has_restore_action_and_blocks_active_board(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    project = _connect_project(database_path, tmp_path / "workspace-archived-repo")
    db.create_task(
        database_path,
        description="Archived project evidence",
        status="Done",
        metadata=project_task_metadata(project),
    )
    db.archive_connected_project(database_path, project["id"])

    with _client(tmp_path) as client:
        workspace = client.get(f"/api/projects/{project['id']}/workspace", headers=_portal_headers())
        board = client.get(f"/api/projects/{project['id']}/board", headers=_portal_headers())
        history = client.get(f"/api/projects/{project['id']}/task-history", headers=_portal_headers())

    assert workspace.status_code == 200
    workspace_payload = workspace.json()
    assert workspace_payload["project"]["archived_at"] is not None
    assert workspace_payload["controls"]["can_restore"] is True
    assert workspace_payload["controls"]["can_open_board"] is False
    assert workspace_payload["links"]["restore_href"] == f"/projects/{project['id']}/restore"
    assert workspace_payload["links"]["board_href"] is None
    assert any(
        "Restore this project before launching new Worker work" in a["detail"]
        for a in workspace_payload["summary"]["attention_actions"]
    )
    assert board.status_code == 409
    assert history.status_code == 200
    history_payload = history.json()
    assert any("Archived project evidence" in t["description"] for t in history_payload["tasks"])


def test_connecting_archived_root_restores_existing_project_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    root = tmp_path / "reopen-archived-repo"
    project = _connect_project(database_path, root)
    db.archive_connected_project(database_path, project["id"])

    with _client(tmp_path) as client:
        response = client.post(
            "/settings/project/connect?redirect=workspace",
            headers={**_portal_headers(), "Accept": "text/html"},
            data={"root_path": str(root)},
            follow_redirects=False,
        )

    restored = db.get_connected_project(database_path, project["id"])
    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{project['id']}"
    assert restored["archived_at"] is None
    assert db.list_archived_connected_projects(database_path) == []
