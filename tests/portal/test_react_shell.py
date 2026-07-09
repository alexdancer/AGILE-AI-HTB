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


def test_react_shell_served_when_built(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path) as client:
        shell = client.get("/app/projects/1", headers=_portal_headers())
        asset = client.get("/static/react/assets/main.js")

    assert shell.status_code == 200
    assert 'id="root"' in shell.text
    assert asset.status_code == 200
    assert "react shell" in asset.text


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
