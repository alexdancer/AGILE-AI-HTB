from pathlib import Path

import pytest

from agile_ai_htb import db
from agile_ai_htb.project_context import project_task_metadata
from agile_ai_htb.routes import react_shell
from tests.portal.helpers import (
    PORTAL_TOKEN,
    _client,
    _connect_project,
    _portal_headers,
)


def _build_react_assets(tmp_path):
    build_dir = tmp_path / "react_build"
    (build_dir / "assets").mkdir(parents=True)
    (build_dir / "index.html").write_text(
        '<!doctype html><div id="root"></div>'
        '<script type="module" src="/static/react/assets/main.js"></script>',
        encoding="utf-8",
    )
    (build_dir / "assets" / "main.js").write_text(
        "console.log('react shell');", encoding="utf-8"
    )
    return build_dir


def _build_partial_react_assets(tmp_path):
    build_dir = tmp_path / "partial_react_build"
    build_dir.mkdir(parents=True)
    (build_dir / "index.html").write_text(
        '<!doctype html><div id="root"></div>'
        '<script type="module" src="/static/react/assets/missing.js"></script>',
        encoding="utf-8",
    )
    return build_dir


def test_react_shell_served_when_built(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path) as client:
        shells = [
            client.get(path, headers=_portal_headers())
            for path in ("/app", "/app/projects/1", "/app/projects/1/board")
        ]
        asset = client.get("/static/react/assets/main.js")

    assert all(shell.status_code == 200 for shell in shells)
    assert all('id="root"' in shell.text for shell in shells)
    assert asset.status_code == 200
    assert "react shell" in asset.text


@pytest.mark.parametrize(
    "path",
    [
        "/app/settings",
        "/app/not-a-migrated-route",
        "/app/projects/demo-999/extra",
        "/app/projects/demo-999/board/extra",
    ],
)
def test_react_shell_rejects_unknown_routes(path, tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)

    with _client(tmp_path) as client:
        response = client.get(path, headers=_portal_headers())

    assert response.status_code == 404


def test_react_shell_reports_missing_build(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    empty_dir = tmp_path / "no_build"
    empty_dir.mkdir()
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: empty_dir)
    with _client(tmp_path) as client:
        response = client.get("/app/projects/1", headers=_portal_headers())

    assert response.status_code == 503
    assert "not built" in response.text
    # Never a silent blank shell.
    assert "<h1>" in response.text


def test_partial_react_build_falls_back_without_blank_shell(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_partial_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)

    with _client(tmp_path, portal_auth_required=False) as client:
        root = client.get("/", follow_redirects=False)

    with _client(tmp_path) as client:
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )
        shell = client.get("/app", headers=_portal_headers())

    assert root.headers["location"] == "/projects"
    assert login.status_code == 303
    assert login.headers["location"] == "/projects"
    assert shell.status_code == 503
    assert "not built" in shell.text


def test_landing_uses_jinja_even_when_react_built(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path, portal_auth_required=False) as client:
        root = client.get("/", follow_redirects=False)

    assert root.status_code in (302, 307)
    # The Jinja landing is the default even when the React build is present.
    assert root.headers["location"] == "/projects"


def test_authenticated_root_uses_jinja_even_when_react_built(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path) as client:
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )
        root = client.get("/", follow_redirects=False)

    assert login.status_code == 303
    assert root.status_code in (302, 307)
    # Authenticated root must not land on the incomplete React /app surface.
    assert root.headers["location"] == "/projects"


def test_landing_falls_back_to_jinja_when_build_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    # The autouse fixture pins the build as absent; the Jinja landing survives.
    with _client(tmp_path, portal_auth_required=False) as client:
        root = client.get("/", follow_redirects=False)
        landing = client.get(root.headers["location"])

    assert root.headers["location"] == "/projects"
    assert landing.status_code == 200
    assert "<html" in landing.text.lower()


def test_authenticated_root_falls_back_to_jinja_when_build_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )
        root = client.get("/", follow_redirects=False)

    assert login.status_code == 303
    assert root.headers["location"] == "/projects"


def test_login_redirects_to_jinja_even_when_react_built(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path) as client:
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )

    assert login.status_code == 303
    assert login.headers["location"] == "/projects"
    assert "agile_ai_htb_portal" in login.headers.get("set-cookie", "")


def test_built_react_and_valid_cookie_lands_on_jinja_not_app(tmp_path, monkeypatch):
    # Regression lock: a built React shell plus a valid signed portal cookie
    # must still land on the server-rendered project page, never /app, until
    # React Portal parity gates pass (see docs/REACT_PORTAL_PARITY_PLAN.md).
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        # Perform a real login so the signed cookie is set on the client.
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )
        assert login.status_code == 303
        assert "agile_ai_htb_portal" in login.headers.get("set-cookie", "")
        # Authenticated root must redirect to the Jinja project landing.
        root = client.get("/", follow_redirects=False)
        landing = client.get(root.headers["location"], follow_redirects=False)

    assert login.headers["location"] == f"/projects/{project['id']}"
    assert root.status_code in (302, 307)
    assert root.headers["location"] == f"/projects/{project['id']}"
    assert landing.status_code == 200
    assert "<html" in landing.text.lower()


def test_login_falls_back_to_jinja_when_build_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )

    assert login.status_code == 303
    assert login.headers["location"] == "/projects"


def test_react_projects_endpoint_requires_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/api/projects")

    assert response.status_code == 401


def test_react_projects_endpoint_lists_connected_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        response = client.get("/api/projects", headers=_portal_headers())

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["projects"]) == 1
    listed = payload["projects"][0]
    assert listed["id"] == project["id"]
    assert listed["name"] == project["name"]
    assert set(listed["counts"]) == {
        "Estimated",
        "Running",
        "Review",
        "Done",
        "Blocked",
    }
    assert listed["total_tasks"] == sum(listed["counts"].values())


def test_react_projects_endpoint_empty_list(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/api/projects", headers=_portal_headers())

    assert response.status_code == 200
    assert response.json() == {"projects": []}


def test_react_json_endpoints_require_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        workspace = client.get("/api/projects/1/workspace")
        board = client.get("/api/projects/1/board")
        shell = client.get("/app/projects/1")

    assert workspace.status_code == 401
    assert board.status_code == 401
    assert shell.status_code == 401


def test_react_workspace_state_reuses_project_helpers(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        response = client.get(
            f"/api/projects/{project['id']}/workspace", headers=_portal_headers()
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"]["id"] == project["id"]
    assert set(payload["summary"]["counts"]) == {
        "Estimated",
        "Running",
        "Review",
        "Done",
        "Blocked",
    }
    assert "launch_ready" in payload["summary"]


def test_react_board_state_reuses_board_context(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        response = client.get(
            f"/api/projects/{project['id']}/board", headers=_portal_headers()
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"]["id"] == project["id"]
    assert payload["columns"] == [
        "Estimated",
        "Running",
        "Review",
        "Done",
        "Blocked",
    ]
    assert set(payload["tasks_by_status"]) == set(payload["columns"])
    assert "board_empty_states" in payload


def test_react_board_state_and_frontend_use_estimate_token_field(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        task = db.create_task(
            database_path,
            description="Display estimated token field in React board",
            status="Estimated",
            estimate_tokens=9_999,
            metadata=project_task_metadata(project),
        )
        response = client.get(
            f"/api/projects/{project['id']}/board", headers=_portal_headers()
        )

    assert response.status_code == 200
    estimated = response.json()["tasks_by_status"]["Estimated"][0]
    assert estimated["id"] == task["id"]
    assert estimated["description"] == "Display estimated token field in React board"
    assert estimated["estimate_tokens"] == 9_999
    assert "estimated_tokens" not in estimated

    board_source = Path("frontend/src/views/Board.jsx").read_text(encoding="utf-8")
    assert "task.description" in board_source
    assert "task.title" not in board_source
    assert "task.estimate_tokens" in board_source
    assert "task.estimated_tokens" not in board_source
    assert 'name="auto_agent_review"' in board_source


def test_react_json_missing_project_is_404(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get(
            "/api/projects/does-not-exist/workspace", headers=_portal_headers()
        )

    assert response.status_code == 404


def test_jinja_project_pages_remain_available(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        workspace = client.get(
            f"/projects/{project['id']}", headers=_portal_headers()
        )
        board = client.get(
            f"/projects/{project['id']}/board", headers=_portal_headers()
        )

    # Non-migrated Jinja surfaces still render server-side without a React build.
    assert workspace.status_code == 200
    assert "<html" in workspace.text.lower()
    assert board.status_code == 200


def test_portal_nav_requires_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/api/portal/nav")

    assert response.status_code == 401


def test_portal_nav_shape(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        # No projects connected yet.
        empty = client.get("/api/portal/nav", headers=_portal_headers())
        assert empty.status_code == 200
        body = empty.json()
        assert body["portal_auth_required"] is True
        assert body["sidebar_projects"] == []

        # Connect a project and re-request.
        project = _connect_project(database_path, tmp_path / "repo")
        populated = client.get("/api/portal/nav", headers=_portal_headers())
        assert populated.status_code == 200
        projects = populated.json()["sidebar_projects"]
        assert len(projects) == 1
        item = projects[0]
        assert item["id"] == str(project["id"])
        assert item["name"] == project["name"]
        assert "task_count" in item
        assert populated.json()["portal_auth_required"] is True


def test_portal_nav_auth_disabled_no_projects(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path, portal_auth_required=False) as client:
        response = client.get("/api/portal/nav")

    assert response.status_code == 200
    body = response.json()
    assert body["portal_auth_required"] is False
    assert body["sidebar_projects"] == []


def test_react_shell_chrome_contract():
    """Frontend source-contract: Shell.jsx renders the full Portal chrome."""
    shell_source = Path("frontend/src/components/Shell.jsx").read_text(encoding="utf-8")
    # Sidebar groups and labels mirroring base.html.
    assert "Projects" in shell_source
    assert "+ Open local repo" in shell_source
    assert "First-run setup" in shell_source
    assert "Dashboard" in shell_source
    assert "Sessions" in shell_source
    assert "Alarms" in shell_source
    assert "Control plane model" in shell_source
    assert "Token budget" in shell_source
    assert "Worker adapters" in shell_source
    # Footer contract.
    assert "AGILE-AI-HTB portal · operator-controlled budget governance" in shell_source
    # Logout form posts to /logout.
    assert 'action="/logout"' in shell_source
    # Task board / No tasks subtitle contract.
    assert "Task board" in shell_source
    assert "No tasks" in shell_source
    # Sidebar nav endpoint.
    assert "/api/portal/nav" in shell_source


def test_react_shell_non_migrated_links_are_anchors():
    """Non-migrated Jinja routes render as full-page <a href>, not AppLink."""
    shell_source = Path("frontend/src/components/Shell.jsx").read_text(encoding="utf-8")
    for jinja_href in (
        "/setup",
        "/dashboard",
        "/sessions",
        "/alarms",
        "/settings/control-plane",
        "/settings/budget",
        "/settings/project",
        "/settings/workers",
        "/board",
        "/projects",
    ):
        assert f'href="{jinja_href}"' in shell_source


def test_css_shell_layout_present():
    """tokens.css includes the .shell grid layout mirroring base.html."""
    css_source = Path("frontend/src/tokens.css").read_text(encoding="utf-8")
    assert ".shell" in css_source
    assert ".sidebar" in css_source
    assert ".project-item" in css_source
    assert ".project-board" in css_source
    assert ".sidebar-action" in css_source
    assert ".shell-footer" in css_source
    assert ".logout" in css_source
    assert "@media (max-width: 900px)" in css_source