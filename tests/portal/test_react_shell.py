import json
from pathlib import Path

import pytest

from foreman_ai_hq import db
from foreman_ai_hq.project_context import project_task_metadata
from foreman_ai_hq.routes import react_shell
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


def _build_mixed_quote_partial_react_assets(tmp_path):
    build_dir = tmp_path / "mixed_quote_partial_react_build"
    (build_dir / "assets").mkdir(parents=True)
    (build_dir / "index.html").write_text(
        '<!doctype html><div id="root"></div>'
        '<script type="module" src="/static/react/assets/main.js"></script>'
        "<link rel='stylesheet' href='/static/react/assets/missing.css'>",
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
        login_form = client.get("/login", follow_redirects=False)
        login_submit = client.post(
            "/login",
            data={"token": "unused-DEMO-999"},
            follow_redirects=False,
        )
        logout = client.post("/logout", follow_redirects=False)
        landing = client.get(root.headers["location"])

    with _client(tmp_path) as client:
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )
        authenticated_root = client.get("/", follow_redirects=False)
        shell = client.get("/app", headers=_portal_headers())

    assert root.headers["location"] == "/projects"
    assert login_form.headers["location"] == "/projects"
    assert login_submit.headers["location"] == "/projects"
    assert logout.headers["location"] == "/projects"
    assert landing.status_code == 200
    assert login.status_code == 303
    assert login.headers["location"] == "/projects"
    assert authenticated_root.headers["location"] == "/projects"
    assert shell.status_code == 503
    assert "not built" in shell.text


def test_partial_react_build_uses_connected_project_fallback_for_all_entries(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_partial_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    database_path = tmp_path / "harness.db"

    with _client(tmp_path, portal_auth_required=False) as client:
        project = _connect_project(database_path, tmp_path / "partial-fallback-repo")
        no_auth_responses = [
            client.get("/", follow_redirects=False),
            client.get("/login", follow_redirects=False),
            client.post(
                "/login",
                data={"token": "unused-DEMO-999"},
                follow_redirects=False,
            ),
            client.post("/logout", follow_redirects=False),
        ]

    with _client(tmp_path) as client:
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )
        authenticated_root = client.get("/", follow_redirects=False)

    expected = f"/projects/{project['id']}"
    assert all(response.headers["location"] == expected for response in no_auth_responses)
    assert login.headers["location"] == expected
    assert authenticated_root.headers["location"] == expected


def test_mixed_quote_missing_asset_rejects_partial_build(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_mixed_quote_partial_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)

    with _client(tmp_path, portal_auth_required=False) as client:
        root = client.get("/", follow_redirects=False)
        shell = client.get("/app")

    assert root.headers["location"] == "/projects"
    assert shell.status_code == 503


def test_auth_disabled_root_uses_react_when_built(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path, portal_auth_required=False) as client:
        root = client.get("/", follow_redirects=False)

    assert root.status_code in (302, 307)
    assert root.headers["location"] == "/app"


def test_auth_disabled_login_and_logout_use_react_when_built(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)

    with _client(tmp_path, portal_auth_required=False) as client:
        login_form = client.get("/login", follow_redirects=False)
        login_submit = client.post(
            "/login",
            data={"token": "unused-DEMO-999"},
            follow_redirects=False,
        )
        logout = client.post("/logout", follow_redirects=False)

    assert login_form.headers["location"] == "/app"
    assert login_submit.headers["location"] == "/app"
    assert logout.headers["location"] == "/app"


def test_authenticated_root_uses_react_when_built(tmp_path, monkeypatch):
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
    assert root.headers["location"] == "/app"


@pytest.mark.parametrize(
    "build_helper",
    [_build_react_assets, _build_partial_react_assets],
)
def test_react_build_availability_never_bypasses_root_auth(
    build_helper,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = build_helper(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)

    with _client(tmp_path) as client:
        root = client.get("/", follow_redirects=False)

    assert root.status_code in (302, 307)
    assert root.headers["location"] == "/login"


def test_landing_falls_back_to_jinja_when_build_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    # The autouse fixture pins the build as absent; the Jinja landing survives.
    with _client(tmp_path, portal_auth_required=False) as client:
        root = client.get("/", follow_redirects=False)
        landing = client.get(root.headers["location"])

    assert root.headers["location"] == "/projects"
    assert landing.status_code == 200
    assert "<html" in landing.text.lower()


def test_missing_build_falls_back_to_connected_project_for_all_no_auth_entries(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"

    with _client(tmp_path, portal_auth_required=False) as client:
        project = _connect_project(database_path, tmp_path / "fallback-repo")
        root = client.get("/", follow_redirects=False)
        login_form = client.get("/login", follow_redirects=False)
        login_submit = client.post(
            "/login",
            data={"token": "unused-DEMO-999"},
            follow_redirects=False,
        )
        logout = client.post("/logout", follow_redirects=False)

    expected = f"/projects/{project['id']}"
    assert root.headers["location"] == expected
    assert login_form.headers["location"] == expected
    assert login_submit.headers["location"] == expected
    assert logout.headers["location"] == expected


def test_authenticated_root_falls_back_to_jinja_when_build_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )
        root = client.get("/", follow_redirects=False)

    assert login.status_code == 303
    assert root.headers["location"] == "/projects"


def test_login_redirects_to_react_when_built(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path) as client:
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )

    assert login.status_code == 303
    assert login.headers["location"] == "/app"
    assert "foreman_ai_hq_portal" in login.headers.get("set-cookie", "")


def test_built_react_and_valid_cookie_lands_on_app(tmp_path, monkeypatch):
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
        assert "foreman_ai_hq_portal" in login.headers.get("set-cookie", "")
        root = client.get("/", follow_redirects=False)
        landing = client.get(root.headers["location"], follow_redirects=False)

    assert project["id"]
    assert login.headers["location"] == "/app"
    assert root.status_code in (302, 307)
    assert root.headers["location"] == "/app"
    assert landing.status_code == 200
    assert 'id="root"' in landing.text


def test_login_falls_back_to_jinja_when_build_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        login = client.post(
            "/login", data={"token": PORTAL_TOKEN}, follow_redirects=False
        )

    assert login.status_code == 303
    assert login.headers["location"] == "/projects"


def test_non_migrated_jinja_routes_remain_directly_reachable(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"

    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "jinja-fallback-repo")
        session = db.create_session(
            database_path,
            task_description="DEMO session report 999",
            model="DEMO-model-999",
            session_key_hash="DEMO-hash-999",
            guardrail_overrides={},
            status="completed",
        )
        breakdown = db.create_task_breakdown(
            database_path,
            source_text="# DEMO breakdown 999",
            source_sha256="DEMO-sha-999",
            intake_metadata={},
            status="pending_review",
            decision="single_task",
            model="DEMO-model-999",
            candidates=[],
        )
        headers = {**_portal_headers(), "Accept": "text/html"}
        paths = [
            "/dashboard",
            "/projects",
            f"/projects/{project['id']}",
            f"/projects/{project['id']}/board",
            "/sessions",
            f"/sessions/{session['id']}",
            "/alarms",
            "/setup",
            "/settings/control-plane",
            "/settings/budget",
            "/settings/project",
            "/settings/workers",
            f"/projects/{project['id']}/task-history",
            f"/task-breakdowns/{breakdown['id']}/review",
        ]
        responses = {path: client.get(path, headers=headers) for path in paths}

    assert {path: response.status_code for path, response in responses.items()} == {
        path: 200 for path in paths
    }


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


def test_react_dashboard_endpoint_requires_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/api/dashboard")

    assert response.status_code == 401


def test_react_dashboard_projection_is_safe_and_matches_jinja(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        session = db.create_session(
            database_path,
            task_description="React dashboard active session",
            model="opencode/gpt-5.1",
            session_key_hash="dashboard-secret-hash",
            guardrail_overrides={"private": "do-not-return"},
            status="running",
        )
        db.record_token_turn(
            database_path,
            session_id=session["id"],
            model="opencode/gpt-5.1",
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.01,
            raw_usage={
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
                "private": "do-not-return",
            },
        )
        db.record_alarm(
            database_path,
            session_id=session["id"],
            alarm={
                "id": "react-dashboard-open",
                "type": "BUDGET_YELLOW",
                "severity": "LOW",
                "context": {"private": "do-not-return"},
                "recommended_action": "Review spend.",
            },
        )
        db.record_alarm(
            database_path,
            session_id=session["id"],
            alarm={
                "id": "react-dashboard-resolved",
                "type": "BUDGET_RED",
                "severity": "HIGH",
                "context": {},
                "recommended_action": "Stop launches.",
            },
        )
        db.resolve_alarm(
            database_path,
            alarm_id="react-dashboard-resolved",
            action="continue",
        )
        db.create_task(
            database_path,
            description="Accuracy parity",
            status="Done",
            estimate_tokens=100,
            actual_tokens=150,
        )

        api = client.get("/api/dashboard", headers=_portal_headers())
        jinja = client.get("/dashboard", headers=_portal_headers())

    assert api.status_code == 200
    assert jinja.status_code == 200
    payload = api.json()
    assert set(payload) == {
        "next_actions",
        "budget",
        "worker_execution",
        "spend",
        "alarms",
        "active_sessions",
        "estimation_accuracy",
        "projects",
    }
    assert set(payload["next_actions"][0]) == {"label", "detail", "href", "tone"}
    assert set(payload["budget"]) == {"total_tokens", "daily_cap", "current_zone", "since"}
    assert set(payload["worker_execution"]) == {"token_total", "status_split", "components"}
    assert set(payload["worker_execution"]["status_split"]) == {
        "completed",
        "failed_retry",
        "unknown",
    }
    assert set(payload["worker_execution"]["components"]) == {"available", "items", "cost"}
    component_items = payload["worker_execution"]["components"]["items"]
    assert component_items
    assert all(set(item) == {"label", "value"} for item in component_items)
    assert set(payload["spend"]) == {
        "worker_execution",
        "agent_review_reporting",
        "planning_estimation",
        "setup_verification",
        "other",
    }
    assert set(payload["alarms"]) == {"total", "open", "critical", "recent"}
    assert payload["budget"]["total_tokens"] == 150
    assert payload["worker_execution"]["token_total"] == 150
    assert payload["active_sessions"] == [
        {
            "id": session["id"],
            "task_description": "React dashboard active session",
            "model": "opencode/gpt-5.1",
            "status": "running",
        }
    ]
    assert payload["alarms"]["recent"] == [
        {
            "id": "react-dashboard-open",
            "type": "BUDGET_YELLOW",
            "severity": "LOW",
            "session_id": session["id"],
            "recommended_action": "Review spend.",
        }
    ]
    assert payload["estimation_accuracy"] == {
        "completed_count": 1,
        "median_error_ratio": 1.5,
        "within_2x_pct": 100.0,
    }
    assert payload["projects"][0]["id"] == project["id"]
    assert payload["projects"][0]["name"] == project["name"]
    assert payload["projects"][0]["task_count"] == 0
    assert set(payload["projects"][0]) == {"id", "name", "task_count", "capability"}
    assert set(payload["projects"][0]["capability"]) == {"state"}
    serialized = json.dumps(payload)
    assert "dashboard-secret-hash" not in serialized
    assert "do-not-return" not in serialized
    assert "root_path" not in serialized
    for action in payload["next_actions"]:
        assert action["label"] in jinja.text
    assert payload["budget"]["since"] in jinja.text
    assert "150" in jinja.text
    assert session["id"] in jinja.text
    assert "react-dashboard-open" in jinja.text
    assert "react-dashboard-resolved" not in jinja.text


def test_react_dashboard_previews_are_newest_first_bounded_and_unresolved(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    sessions = []
    with _client(tmp_path) as client:
        for index in range(6):
            session = db.create_session(
                database_path,
                task_description=f"Dashboard session {index}",
                model="opencode/gpt-5.1",
                session_key_hash=f"dashboard-hash-{index}",
                guardrail_overrides={},
                status="running",
            )
            sessions.append(session)
            db.record_alarm(
                database_path,
                session_id=session["id"],
                alarm={
                    "id": f"dashboard-alarm-{index}",
                    "type": "BUDGET_YELLOW",
                    "severity": "LOW",
                    "context": {},
                    "recommended_action": "Review spend.",
                },
            )
        with db.connect(database_path) as conn:
            for index, session in enumerate(sessions):
                timestamp = f"2099-01-01T00:00:0{index}+00:00"
                conn.execute("update sessions set started_at = ? where id = ?", (timestamp, session["id"]))
                conn.execute(
                    "update alarms set created_at = ? where id = ?",
                    (timestamp, f"dashboard-alarm-{index}"),
                )
        db.resolve_alarm(
            database_path,
            alarm_id="dashboard-alarm-0",
            action="continue",
        )
        response = client.get("/api/dashboard", headers=_portal_headers())

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["active_sessions"]] == [
        session["id"] for session in reversed(sessions[1:])
    ]
    assert [item["id"] for item in payload["alarms"]["recent"]] == [
        f"dashboard-alarm-{index}" for index in range(5, 0, -1)
    ]


def test_react_json_endpoints_require_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        dashboard = client.get("/api/dashboard")
        workspace = client.get("/api/projects/1/workspace")
        board = client.get("/api/projects/1/board")
        shell = client.get("/app/projects/1")

    assert dashboard.status_code == 401
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


def test_react_workspace_state_uses_exact_contract_and_route_ownership(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "workspace-contract-repo")
        db.create_task(
            database_path,
            description="DEMO running workspace slice 999",
            status="Running",
            metadata=project_task_metadata(project),
        )
        response = client.get(
            f"/api/projects/{project['id']}/workspace", headers=_portal_headers()
        )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"project", "summary", "controls", "links"}
    assert set(payload["project"]) == {
        "id", "name", "root_path", "archived_at", "capability", "profile",
    }
    assert set(payload["project"]["capability"]) == {"state", "label", "reasons"}
    assert set(payload["project"]["profile"]) == {
        "git_branch", "language_hints", "framework_hints", "package_manager_hints",
        "test_command", "run_command", "relevant_docs",
    }
    assert set(payload["summary"]) == {
        "counts", "total_tasks", "launch_ready", "capability_state", "attention_actions",
    }
    assert set(payload["summary"]["counts"]) == {
        "Estimated", "Running", "Review", "Done", "Blocked",
    }
    assert set(payload["controls"]) == {"can_open_board", "can_restore"}
    assert set(payload["links"]) == {
        "board_href", "task_history_href", "sessions_href", "worker_setup_href",
        "project_settings_href", "restore_href",
    }
    assert payload["controls"] == {"can_open_board": True, "can_restore": False}
    assert payload["links"] == {
        "board_href": f"/app/projects/{project['id']}/board",
        "task_history_href": f"/projects/{project['id']}/task-history",
        "sessions_href": "/sessions",
        "worker_setup_href": "/settings/workers",
        "project_settings_href": "/settings/project",
        "restore_href": None,
    }
    running = next(
        action for action in payload["summary"]["attention_actions"]
        if action["label"] == "Running work"
    )
    assert running["href"] == f"/app/projects/{project['id']}/board"
    assert set(running) == {"label", "detail", "href", "tone"}
    serialized = json.dumps(payload)
    for excluded in (
        "backend_id", "archived_by", "created_at", "updated_at", "can_launch",
    ):
        assert excluded not in serialized


def test_react_workspace_projection_applies_every_bound_and_redacts():
    project_id = "project-" + "9" * 200
    bounded_id = project_id[:128]
    safe_long = "x" * 5000
    action = {
        "label": "l" * 500,
        "detail": "d" * 1500,
        "href": f"/projects/{bounded_id}/board",
        "tone": "t" * 100,
    }
    payload = react_shell._react_workspace_projection(
        {
            "id": project_id,
            "name": "n" * 500,
            "root_path": safe_long,
            "archived_at": None,
            "capability": {
                "state": "s" * 100,
                "label": "c" * 500,
                "reasons": ["r" * 1500 for _ in range(25)],
                "secret": "DEMO_CAPABILITY_SECRET_999",
            },
            "profile": {
                "git_branch": "b" * 800,
                "language_hints": ["l" * 300 for _ in range(25)],
                "framework_hints": ["f" * 300 for _ in range(25)],
                "package_manager_hints": ["p" * 300 for _ in range(25)],
                "test_command": "t" * 5000,
                "run_command": "password=DEMO_RUN_SECRET_999 " + safe_long,
                "relevant_docs": ["d" * 1500 for _ in range(60)],
                "internal_config": {"token": "DEMO_PROFILE_SECRET_999"},
            },
            "backend_id": "DEMO_BACKEND_SECRET_999",
        },
        {
            "counts": {
                "Estimated": 1,
                "Running": -1,
                "Review": True,
                "Done": "4",
                "Blocked": 5,
            },
            "launch_ready": True,
            "capability_state": "q" * 100,
            "attention_actions": [
                {**action, "href": "/unsafe/path"},
                *[action for _ in range(25)],
            ],
            "command_plan": {"token": "DEMO_SUMMARY_SECRET_999"},
        },
    )

    project = payload["project"]
    profile = project["profile"]
    capability = project["capability"]
    summary = payload["summary"]
    assert len(project["id"]) == 128
    assert len(project["name"]) == 200
    assert len(project["root_path"]) == 4096
    assert len(capability["state"]) == 64
    assert len(capability["label"]) == 200
    assert len(capability["reasons"]) == 20
    assert all(len(item) == 1000 for item in capability["reasons"])
    assert len(profile["git_branch"]) == 500
    for key in ("language_hints", "framework_hints", "package_manager_hints"):
        assert len(profile[key]) == 20
        assert all(len(item) == 200 for item in profile[key])
    assert len(profile["test_command"]) == 4000
    assert len(profile["run_command"]) <= 4000
    assert len(profile["relevant_docs"]) == 50
    assert all(len(item) == 1000 for item in profile["relevant_docs"])
    assert summary["counts"] == {
        "Estimated": 1, "Running": 0, "Review": 0, "Done": 0, "Blocked": 5,
    }
    assert summary["total_tasks"] == 6
    assert len(summary["capability_state"]) == 64
    assert len(summary["attention_actions"]) == 20
    assert all(len(item["label"]) == 200 for item in summary["attention_actions"])
    assert all(len(item["detail"]) == 1000 for item in summary["attention_actions"])
    assert all(len(item["tone"]) == 32 for item in summary["attention_actions"])
    assert all(
        item["href"] == f"/app/projects/{bounded_id}/board"
        for item in summary["attention_actions"]
    )
    serialized = json.dumps(payload)
    for secret in (
        "DEMO_RUN_SECRET_999", "DEMO_CAPABILITY_SECRET_999", "DEMO_PROFILE_SECRET_999",
        "DEMO_BACKEND_SECRET_999", "DEMO_SUMMARY_SECRET_999",
    ):
        assert secret not in serialized


def test_react_workspace_projection_uses_typed_defaults_for_malformed_values():
    payload = react_shell._react_workspace_projection(
        {
            "id": "project-DEMO-999",
            "name": ["bad"],
            "root_path": {"bad": True},
            "archived_at": {"bad": True},
            "capability": "bad",
            "profile": "bad",
        },
        {
            "counts": "bad",
            "launch_ready": "yes",
            "capability_state": ["bad"],
            "attention_actions": "bad",
        },
    )

    assert payload["project"] == {
        "id": "project-DEMO-999",
        "name": "",
        "root_path": "",
        "archived_at": None,
        "capability": {"state": "", "label": "", "reasons": []},
        "profile": {
            "git_branch": None,
            "language_hints": [],
            "framework_hints": [],
            "package_manager_hints": [],
            "test_command": None,
            "run_command": None,
            "relevant_docs": [],
        },
    }
    assert payload["summary"] == {
        "counts": {column: 0 for column in (
            "Estimated", "Running", "Review", "Done", "Blocked"
        )},
        "total_tasks": 0,
        "launch_ready": False,
        "capability_state": "",
        "attention_actions": [],
    }


    archived = react_shell._react_workspace_projection(
        {
            "id": "project-DEMO-999",
            "name": "DEMO archived project",
            "root_path": "/DEMO/2099/repo",
            "archived_at": "a" * 100,
            "capability": {},
            "profile": {},
        },
        {},
    )
    assert len(archived["project"]["archived_at"]) == 64
    assert archived["controls"] == {"can_open_board": False, "can_restore": True}


def test_react_workspace_endpoint_tolerates_malformed_stored_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "malformed-workspace-repo")
        with db.connect(database_path) as conn:
            conn.execute(
                "update connected_projects set profile_json = ?, capability_json = ? where id = ?",
                ('"bad-profile"', '"bad-capability"', project["id"]),
            )
        response = client.get(
            f"/api/projects/{project['id']}/workspace", headers=_portal_headers()
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"]["profile"] == {
        "git_branch": None,
        "language_hints": [],
        "framework_hints": [],
        "package_manager_hints": [],
        "test_command": None,
        "run_command": None,
        "relevant_docs": [],
    }
    assert set(payload["project"]["capability"]) == {"state", "label", "reasons"}


def test_react_archived_workspace_is_restore_first(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "react-archived-repo")
        db.archive_connected_project(database_path, project["id"])
        workspace = client.get(
            f"/api/projects/{project['id']}/workspace", headers=_portal_headers()
        )
        board = client.get(
            f"/api/projects/{project['id']}/board", headers=_portal_headers()
        )

    assert workspace.status_code == 200
    payload = workspace.json()
    assert payload["project"]["archived_at"]
    assert payload["summary"]["launch_ready"] is False
    assert payload["summary"]["capability_state"] == "archived"
    assert payload["controls"] == {"can_open_board": False, "can_restore": True}
    assert payload["links"]["board_href"] is None
    assert payload["links"]["restore_href"] == f"/projects/{project['id']}/restore"
    assert board.status_code == 409
    assert "restore archived project" in board.json()["detail"]


def test_react_restore_json_success_is_idempotent_and_bounded(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    headers = {**_portal_headers(), "Accept": "application/json"}
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "react-restore-repo")
        db.archive_connected_project(database_path, project["id"])
        restored = client.post(f"/projects/{project['id']}/restore", headers=headers)
        repeated = client.post(f"/projects/{project['id']}/restore", headers=headers)

    expected = {
        "ok": True,
        "error": None,
        "next_href": f"/app/projects/{project['id']}",
        "retry_href": None,
        "project": {"id": project["id"], "archived": False},
    }
    assert restored.status_code == 200
    assert restored.json() == expected
    assert repeated.status_code == 200
    assert repeated.json() == expected
    assert db.get_connected_project(database_path, project["id"])["archived_at"] is None


@pytest.mark.parametrize(
    ("accept", "expected_status"),
    [
        ("Application/JSON", 200),
        ("application/json;q=0", 303),
        ("text/html, application/json; q=0", 303),
        ("text/html, Application/JSON; charset=utf-8; Q=0.5", 200),
    ],
)
def test_react_restore_respects_accept_quality_and_casing(
    tmp_path, monkeypatch, accept, expected_status
):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "react-restore-accept-repo")
        response = client.post(
            f"/projects/{project['id']}/restore",
            headers={**_portal_headers(), "Accept": accept},
            follow_redirects=False,
        )

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["ok"] is True
    else:
        assert response.headers["location"] == f"/projects/{project['id']}"


@pytest.mark.parametrize(
    ("accept", "expects_react_json"),
    [
        ("Application/JSON", True),
        ("application/json;q=0", False),
        ("text/html, application/json; q=0", False),
        ("text/html, Application/JSON; charset=utf-8; Q=0.5", True),
    ],
)
@pytest.mark.parametrize(
    ("path", "data"),
    [
        ("/projects/missing-DEMO-999/tasks/estimate-form", {"description": "DEMO task 999"}),
        ("/tasks/missing-DEMO-999/launch", {}),
        ("/tasks/missing-DEMO-999/refresh", {}),
        ("/tasks/missing-DEMO-999/review", {"action": "save_prompt"}),
    ],
)
def test_react_task_actions_respect_accept_quality_and_casing(
    tmp_path, monkeypatch, accept, expects_react_json, path, data
):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.post(
            path,
            headers={**_portal_headers(), "Accept": accept},
            data=data,
            follow_redirects=False,
        )

    assert ("ok" in response.json()) is expects_react_json


def test_react_restore_json_unknown_project_is_fixed_404(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    headers = {**_portal_headers(), "Accept": "application/json"}
    with _client(tmp_path) as client:
        response = client.post("/projects/missing-DEMO-999/restore", headers=headers)

    assert response.status_code == 404
    assert response.json() == {
        "ok": False,
        "error": "connected project not found",
        "next_href": None,
        "retry_href": "/projects",
        "project": None,
    }


def test_react_restore_does_not_convert_infrastructure_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "react-restore-error-repo")
        monkeypatch.setattr(
            db,
            "restore_connected_project",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("DEMO DB failure 999")),
        )
        with pytest.raises(RuntimeError, match="DEMO DB failure 999"):
            client.post(
                f"/projects/{project['id']}/restore",
                headers={**_portal_headers(), "Accept": "application/json"},
            )


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
    assert estimated["summary"]["text"] == "Display estimated token field in React board"
    assert estimated["estimate_tokens"] == 9_999
    assert "description" not in estimated
    assert "estimated_tokens" not in estimated

    board_source = Path("frontend/src/views/Board.jsx").read_text(encoding="utf-8")
    assert "task.summary.text" in board_source
    assert "task.estimate_tokens" in board_source
    assert "task.estimated_tokens" not in board_source
    assert "Accept: \"application/json\"" in board_source
    assert "status.reload_required" in board_source
    for action_path in (
        "/tasks/estimate-form",
        "/run-next",
        "/queue/start",
        "/queue/stop",
        "/tasks/archive-done",
        "/archive",
        "/tasks/${task.id}/launch",
        "/tasks/${task.id}/refresh",
        "/tasks/${task.id}/review",
    ):
        assert action_path in board_source
    for form_field in (
        'form.set("project_id"',
        'form.set("adapter_id"',
        'form.set("model"',
        'form.set("budget_override"',
        'form.set("native_budget_acknowledged"',
        "review_prompt",
        "blocked_reason",
        "auto_agent_review",
    ):
        assert form_field in board_source


@pytest.mark.parametrize(
    ("metadata_key", "metadata_value"),
    [
        ("workdir_evidence", "bad-shape"),
        ("last_launch_failure", "bad-shape"),
        ("worker_run_events", "bad-shape"),
    ],
)
def test_react_board_projection_tolerates_malformed_nested_metadata(
    tmp_path, monkeypatch, metadata_key, metadata_value
):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        db.create_task(
            database_path,
            description="Malformed metadata must not break project board",
            status="Estimated",
            estimate_tokens=9_999,
            metadata={
                **project_task_metadata(project),
                metadata_key: metadata_value,
            },
        )

        response = client.get(
            f"/api/projects/{project['id']}/board", headers=_portal_headers()
        )

    assert response.status_code == 200
    card = response.json()["tasks_by_status"]["Estimated"][0]
    assert card["details"]["launch"]["workdir"] is None
    assert card["details"]["timeline"] == []


def test_react_board_projection_sanitizes_and_bounds_timeline_labels(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        db.create_task(
            database_path,
            description="Timeline labels stay safe",
            status="Estimated",
            estimate_tokens=9_999,
            metadata={
                **project_task_metadata(project),
                "worker_run_events": [
                    {
                        "created_at": "2099-01-01T00:00:00Z",
                        "kind": "Bearer DEMO_SECRET_999 " + "k" * 200,
                        "title": "password=DEMO_SECRET_999 " + "t" * 500,
                        "detail_summary": "Bearer DEMO_DETAIL_SECRET_999",
                    }
                ],
            },
        )

        response = client.get(
            f"/api/projects/{project['id']}/board", headers=_portal_headers()
        )

    assert response.status_code == 200
    event = response.json()["tasks_by_status"]["Estimated"][0]["details"]["timeline"][0]
    serialized = json.dumps(event)
    assert "DEMO_SECRET_999" not in serialized
    assert "DEMO_DETAIL_SECRET_999" not in serialized
    assert len(event["kind"]) <= 100
    assert len(event["title"]) <= 400


def test_react_board_projection_uses_exact_nested_allowlists_and_safe_evidence():
    columns = ["Estimated", "Running", "Review", "Done", "Blocked"]
    metadata = {
        "review_actions_available": True,
        "budget_override_available": True,
        "native_usage_override_ack_required": True,
        "native_usage_override_ack_text": "Acknowledge DEMO native usage",
        "active_worker_run_id": "wr_DEMO_999",
        "launch_adapter_id": "codex",
        "launch_model": "gpt-5.4",
        "tracking_mode": "native_usage",
        "usage_source": "worker",
        "worker_run_status": "completed",
        "launch_returncode": 0,
        "launch_error": "password=DEMO_LAUNCH_SECRET_999",
        "workdir_evidence": {"configured_workdir": "/tmp/DEMO_2099_repo"},
        "last_launch_failure": {
            "returncode": 1,
            "error": "Bearer DEMO_FAILURE_SECRET_999",
            "stdout": "safe stdout",
            "stderr": "password=DEMO_STDERR_SECRET_999",
        },
        "launch_diagnostic": {
            "summary": "safe diagnostic",
            "next_action": "open setup",
            "setup_href": "/settings/workers?adapter_id=codex",
        },
        "worker_token_components": {
            "available": True,
            "items": [{
                "key": "password=DEMO_TOKEN_KEY_999" + "k" * 200,
                "label": "Bearer DEMO_TOKEN_LABEL_999" + "l" * 300,
                "value": "password=DEMO_TOKEN_VALUE_999" + "v" * 500,
            }],
            "cost": 0.25,
            "turn_count": 2,
        },
        "worker_run_events": [{
            "created_at": f"2099-01-0{index}T00:00:00Z",
            "kind": "worker_event",
            "title": f"event {index}",
            "detail_summary": f"detail {index}",
        } for index in range(1, 8)],
        "review_prompt": "Review DEMO evidence",
        "agent_review": {
            "status": "completed",
            "recommendation": "approve",
            "summary": "safe review",
            "findings": [{
                "severity": "password=DEMO_SEVERITY_SECRET_999",
                "message": "Bearer DEMO_FINDING_SECRET_999",
                "path": "password=DEMO_PATH_SECRET_999" + "p" * 500,
                "line": 99,
            }],
            "review_session_id": "sess_DEMO_999",
            "model": "password=DEMO_MODEL_SECRET_999" + "m" * 300,
            "token_totals": {"total_tokens": 42},
        },
    }
    context = {
        "board_summary": {
            "launch_ready": True, "total_tasks": 1, "counts": {"Review": 1},
            "archived_count": 0, "history_total_tasks": 1,
        },
        "automation_summary": {
            "counts": {"Review": 1}, "eligible_count": 0,
            "queue": {
                "status": "stopped", "auto_agent_review": True,
                "latest_stop_reason": "operator_stop",
            },
            "live_refresh_enabled": False,
        },
        "board_empty_states": {column: f"No {column}" for column in columns},
        "adapters": [{
            "id": "codex", "name": "Codex", "is_default": True, "launchable": True,
            "supported_models": ["gpt-5.4"], "tracking_label": "Native",
            "tracking": {
                "mode": "native_usage", "runtime_request_guardrails": True,
                "accounting": "authoritative", "budget_authoritative": True,
                "launchable_for_board": True,
            },
        }],
        "tasks_by_status": {
            column: ([{
                "id": "task_DEMO_999", "status": "Review", "description": "Review DEMO task",
                "estimate_tokens": 9000, "actual_tokens": 4000,
                "recommended_model": "gpt-5.4", "session_id": "sess_DEMO_999",
                "metadata": metadata,
            }] if column == "Review" else [])
            for column in columns
        },
    }

    payload = react_shell._react_board_projection(
        {"id": "proj_DEMO_999", "name": "DEMO project"}, context
    )
    card = payload["tasks_by_status"]["Review"][0]

    assert set(payload) == {
        "project", "columns", "board_summary", "history_href", "board_empty_states",
        "automation", "adapters", "tasks_by_status",
    }
    assert set(payload["board_summary"]) == {
        "launch_ready", "total_tasks", "counts", "archived_count", "history_total_tasks",
    }
    assert set(payload["automation"]) == {
        "counts", "eligible_count", "queue", "live_refresh_enabled",
    }
    assert set(payload["automation"]["queue"]) == {
        "status", "auto_agent_review", "latest_stop_reason",
    }
    assert set(payload["adapters"][0]) == {
        "id", "name", "is_default", "launchable", "allowed_models", "tracking",
    }
    assert set(card) == {
        "id", "status", "summary", "estimate_tokens", "actual_tokens",
        "recommended_model", "launch_model", "session_href", "controls", "details",
    }
    assert set(card["controls"]) == {
        "can_launch", "can_refresh", "can_save_review_prompt", "can_agent_review",
        "can_mark_done", "can_block", "can_archive", "can_dismiss",
        "budget_override_available", "native_usage_override_ack_required",
        "native_usage_override_ack_text", "setup_href",
    }
    assert set(card["details"]) == {
        "task_body", "token_components", "launch", "timeline", "logs", "review", "blocked",
    }
    assert set(card["details"]["token_components"]) == {
        "available", "items", "cost", "turn_count",
    }
    assert set(card["details"]["launch"]) == {
        "worker_run_id", "adapter_id", "model", "tracking_mode", "usage_source", "status",
        "returncode", "workdir", "error", "blocked_reason", "retryable_failure", "diagnostic",
    }
    assert set(card["details"]["review"]) == {"prompt", "agent_review"}
    assert set(card["details"]["review"]["agent_review"]) == {
        "status", "recommendation", "summary", "failure", "findings",
        "review_session_href", "model", "token_total",
    }
    assert [event["title"] for event in card["details"]["timeline"]] == [
        f"event {index}" for index in range(2, 8)
    ]
    serialized = json.dumps(card)
    for secret in (
        "DEMO_LAUNCH_SECRET_999", "DEMO_FAILURE_SECRET_999", "DEMO_STDERR_SECRET_999",
        "DEMO_TOKEN_KEY_999", "DEMO_TOKEN_LABEL_999", "DEMO_TOKEN_VALUE_999",
        "DEMO_SEVERITY_SECRET_999", "DEMO_FINDING_SECRET_999", "DEMO_PATH_SECRET_999",
        "DEMO_MODEL_SECRET_999",
    ):
        assert secret not in serialized
    token_item = card["details"]["token_components"]["items"][0]
    finding = card["details"]["review"]["agent_review"]["findings"][0]
    assert len(token_item["key"]) <= 100
    assert len(token_item["label"]) <= 200
    assert len(token_item["value"]) <= 400
    assert len(finding["severity"]) <= 40
    assert len(finding["path"]) <= 400
    assert len(card["details"]["review"]["agent_review"]["model"]) <= 200
    assert card["details"]["launch"]["returncode"] == 0
    assert card["details"]["launch"]["retryable_failure"]["returncode"] == 1
    assert card["details"]["token_components"]["cost"] == 0.25
    assert card["details"]["token_components"]["turn_count"] == 2
    assert finding["line"] == 99
    assert card["details"]["review"]["agent_review"]["token_total"] == 42


def test_react_task_projection_rejects_non_numeric_persisted_scalars():
    secret = "password=DEMO_NUMERIC_SECRET_999"
    card = react_shell._react_task({
        "id": "task_DEMO_999",
        "status": "Review",
        "metadata": {
            "launch_returncode": {"secret": secret},
            "last_launch_failure": {"returncode": secret},
            "worker_token_components": {
                "cost": {"secret": secret},
                "turn_count": [secret],
            },
            "agent_review": {
                "findings": [{"message": "DEMO finding", "line": {"secret": secret}}],
                "token_totals": {"total_tokens": secret},
            },
        },
    })

    assert card["details"]["launch"]["returncode"] is None
    assert card["details"]["launch"]["retryable_failure"]["returncode"] is None
    assert card["details"]["token_components"]["cost"] is None
    assert card["details"]["token_components"]["turn_count"] is None
    assert card["details"]["review"]["agent_review"]["findings"][0]["line"] is None
    assert card["details"]["review"]["agent_review"]["token_total"] is None
    assert "DEMO_NUMERIC_SECRET_999" not in json.dumps(card)


def test_react_task_projection_has_stable_null_and_empty_defaults():
    card = react_shell._react_task(
        {"id": "task_DEMO_999", "status": "Blocked", "description": "", "metadata": {}}
    )

    assert card["summary"] == {"text": "", "truncated": False}
    assert card["estimate_tokens"] is None
    assert card["actual_tokens"] is None
    assert card["recommended_model"] is None
    assert card["launch_model"] is None
    assert card["session_href"] is None
    assert card["details"]["token_components"] == {
        "available": False,
        "items": [],
        "cost": None,
        "turn_count": None,
    }
    assert card["details"]["timeline"] == []
    assert card["details"]["review"]["agent_review"]["findings"] == []
    assert card["details"]["review"]["agent_review"]["review_session_href"] is None
    assert card["details"]["blocked"] == {
        "reason": {"text": "", "truncated": False},
        "requires_manual_estimate": False,
    }


def test_react_task_title_preserves_safe_secret_word_and_redacts_embedded_value():
    safe_title = "Implement Secret scanner parity"
    safe_card = react_shell._react_task(
        {
            "id": "task_DEMO_998",
            "status": "Review",
            "description": safe_title,
            "metadata": {},
        }
    )
    card = react_shell._react_task(
        {
            "id": "task_DEMO_999",
            "status": "Review",
            "description": f"{safe_title}; secret=DEMO-TITLE-SECRET-999",
            "metadata": {},
        }
    )

    assert safe_card["summary"]["text"] == safe_title
    assert safe_title in card["summary"]["text"]
    assert "DEMO-TITLE-SECRET-999" not in card["summary"]["text"]
    assert "***REDACTED***" in card["summary"]["text"]


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
    assert "Foreman AI HQ portal · operator-controlled budget governance" in shell_source
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
        "/settings/control-plane",
        "/settings/budget",
        "/settings/project",
        "/settings/workers",
        "/board",
        "/projects",
    ):
        assert f'href="{jinja_href}"' in shell_source


def test_react_dashboard_source_contract():
    app_source = Path("frontend/src/App.jsx").read_text(encoding="utf-8")
    shell_source = Path("frontend/src/components/Shell.jsx").read_text(encoding="utf-8")
    dashboard_source = Path("frontend/src/views/Dashboard.jsx").read_text(encoding="utf-8")

    assert 'view: "dashboard"' in app_source
    assert "<Dashboard />" in app_source
    assert 'to="/app"' in shell_source
    assert 'activeView === "dashboard"' in shell_source
    assert "sidebar-action active" not in shell_source
    assert 'useResource("/api/dashboard")' in dashboard_source
    assert 'href={action.href}' in dashboard_source
    assert "<AppLink" in dashboard_source
    assert "/app/projects/${project.id}" in dashboard_source


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


def test_css_react_board_controls_and_details_present():
    css_source = Path("frontend/src/tokens.css").read_text(encoding="utf-8")
    assert ".card-controls" in css_source
    assert ".check-row" in css_source
    assert ".detail-grid" in css_source
    assert ".btn.danger" in css_source
    assert ".board-input" in css_source
    assert ".board-file::file-selector-button" in css_source
    assert ".raw-evidence" in css_source


def test_canonical_sessions_routes_use_complete_build_and_validate_report(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    db.init_db(tmp_path / "harness.db")
    session = db.create_session(
        tmp_path / "harness.db",
        task_description="DEMO React session 2099",
        model="demo-model-999",
        session_key_hash="s" * 64,
        guardrail_overrides={},
    )
    with _client(tmp_path) as client:
        sessions = client.get("/sessions", headers=_portal_headers())
        report = client.get(f"/sessions/{session['id']}", headers=_portal_headers())
        missing = client.get("/sessions/missing", headers=_portal_headers())
        unauthenticated = client.get("/sessions", follow_redirects=False)
        unknown_alias = client.get("/app/sessions", headers=_portal_headers())
    assert sessions.status_code == report.status_code == 200
    assert '<div id="root"></div>' in sessions.text and '<div id="root"></div>' in report.text
    assert missing.status_code == 404
    assert unauthenticated.status_code in {302, 303, 401}
    assert unknown_alias.status_code == 404


@pytest.mark.parametrize("partial", [True, False])
def test_canonical_sessions_routes_keep_jinja_fallback(tmp_path, monkeypatch, partial):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_partial_react_assets(tmp_path) if partial else tmp_path / "absent"
    build_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    db.init_db(tmp_path / "harness.db")
    session = db.create_session(
        tmp_path / "harness.db",
        task_description="DEMO Jinja fallback 2099",
        model="demo-model-999",
        session_key_hash="s" * 64,
        guardrail_overrides={},
    )
    with _client(tmp_path) as client:
        sessions = client.get("/sessions", headers=_portal_headers())
        report = client.get(f"/sessions/{session['id']}", headers=_portal_headers())
    assert "All sessions" in sessions.text
    assert "Session report" in report.text


def test_react_task_history_endpoint_requires_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/api/projects/does-not-exist/task-history")
    assert response.status_code == 401


def test_react_task_history_json_uses_exact_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        session = db.create_session(
            database_path,
            task_description="DEMO task history session",
            model="demo-model-999",
            session_key_hash="s" * 64,
            guardrail_overrides={},
        )
        task = db.create_task(
            database_path,
            description="DEMO archived history task",
            status="Done",
            estimate_tokens=1_000,
            actual_tokens=2_000,
            recommended_model="demo-model-999",
            session_id=session["id"],
            metadata={
                **project_task_metadata(project),
                "active_worker_run_id": "run-123",
                "blocked_reason": "DEMO blocked reason",
                "requires_manual_estimate": True,
            },
        )
        db.archive_task(database_path, task["id"])
        response = client.get(
            f"/api/projects/{project['id']}/task-history?filter=archived",
            headers=_portal_headers(),
        )
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"filters", "selected_filter", "tasks"}
    assert all(set(filter) == {"label", "value", "count", "active"} for filter in payload["filters"])
    assert payload["selected_filter"] == "archived"
    assert len(payload["tasks"]) == 1
    task = payload["tasks"][0]
    assert set(task) == {
        "id", "description", "status", "archived", "archived_at", "estimate_tokens",
        "actual_tokens", "recommended_model", "session_href", "worker_run_id",
        "blocked_reason", "requires_manual_estimate",
    }
    assert task["status"] == "Done"
    assert task["archived"] is True
    assert task["archived_at"]
    assert task["estimate_tokens"] == 1_000
    assert task["actual_tokens"] == 2_000
    assert task["recommended_model"] == "demo-model-999"
    assert task["session_href"] == f"/sessions/{session['id']}"
    assert task["worker_run_id"] == "run-123"
    assert task["blocked_reason"] == "DEMO blocked reason"
    assert task["requires_manual_estimate"] is True


def test_react_task_history_unknown_project_is_404(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get(
            "/api/projects/does-not-exist/task-history",
            headers=_portal_headers(),
        )
    assert response.status_code == 404


def test_canonical_task_history_route_serves_react_when_built(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        response = client.get(
            f"/projects/{project['id']}/task-history", headers=_portal_headers()
        )
    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text


def test_canonical_task_history_route_keeps_jinja_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_partial_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        response = client.get(
            f"/projects/{project['id']}/task-history", headers=_portal_headers()
        )
    assert response.status_code == 200
    assert "Task history" in response.text


def test_unarchive_task_content_negotiation(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "repo")
        task = db.create_task(
            database_path,
            description="DEMO unarchive task",
            status="Done",
            metadata=project_task_metadata(project),
        )
        db.archive_task(database_path, task["id"])
        json_response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}/unarchive",
            headers={**_portal_headers(), "Accept": "application/json"},
        )
        html_response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}/unarchive",
            headers={**_portal_headers(), "Accept": "text/html"},
            follow_redirects=False,
        )
    assert json_response.status_code == 200
    payload = json_response.json()
    assert set(payload) == {"ok", "task_id", "status", "archived"}
    assert payload["ok"] is True
    assert payload["task_id"] == task["id"]
    assert payload["status"] == "Done"
    assert payload["archived"] is False
    assert html_response.status_code == 303
    assert html_response.headers["location"] == f"/projects/{project['id']}/task-history"


def test_task_history_view_source_contract():
    """Frontend source/contract: no stale field names, all evidence fields rendered."""
    source = Path("frontend/src/views/TaskHistory.jsx").read_text(encoding="utf-8")
    jinja_template = Path("src/foreman_ai_hq/templates/task_history.html").read_text(encoding="utf-8")
    for field in (
        "task.description",
        "task.id",
        "task.status",
        "task.archived",
        "task.archived_at",
        "task.estimate_tokens",
        "task.actual_tokens",
        "task.recommended_model",
        "task.session_href",
        "task.worker_run_id",
        "task.blocked_reason",
        "task.requires_manual_estimate",
    ):
        assert field in source, f"{field} missing from TaskHistory.jsx"
    assert "?filter=" in source
    assert "`/projects/${projectId}/tasks/${taskId}/unarchive`" in source
    assert "Accept: \"application/json\"" in source
    assert "aria-live" in source
    assert "aria-pressed" in source
    assert "colSpan" in source
    assert "filter=" in jinja_template


def test_react_alarms_api_requires_auth_and_bounded_projection(tmp_path, monkeypatch):
    """GET /api/alarms is authenticated and returns bounded projection fields."""
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        project = _connect_project(database_path, tmp_path / "alarms-repo")
        session = db.create_session(
            database_path,
            task_description="Alarm test",
            model="claude-haiku",
            session_key_hash="alarm-hash",
            guardrail_overrides={},
            status="running",
        )
        db.record_alarm(
            database_path,
            session_id=session["id"],
            alarm={
                "id": "alarm-open-1",
                "type": "DAILY_CAP_EXCEEDED",
                "severity": "HIGH",
                "context": {"daily_cap_tokens": 1000, "daily_used_tokens": 100},
                "recommended_action": "Raise daily cap.",
            },
        )
        db.record_alarm(
            database_path,
            session_id=session["id"],
            alarm={
                "id": "alarm-resolved-1",
                "type": "SESSION_CAP_EXCEEDED",
                "severity": "MEDIUM",
                "context": {"session_cap_tokens": 500, "session_used_tokens": 500},
                "recommended_action": "Raise session cap.",
            },
        )
        db.resolve_alarm(
            database_path,
            alarm_id="alarm-resolved-1",
            action="continue",
        )

        no_auth = client.get("/api/alarms")
        open_auth = client.get("/api/alarms?filter=open", headers=_portal_headers())
        resolved_auth = client.get("/api/alarms?filter=resolved", headers=_portal_headers())
        all_auth = client.get("/api/alarms?filter=all", headers=_portal_headers())

    assert no_auth.status_code == 401
    assert open_auth.status_code == 200
    assert resolved_auth.status_code == 200
    assert all_auth.status_code == 200

    payload = open_auth.json()
    assert set(payload) == {"filters", "selected_filter", "alarms"}
    assert payload["selected_filter"] == "open"
    assert len(payload["alarms"]) == 1
    assert payload["alarms"][0]["id"] == "alarm-open-1"
    assert payload["alarms"][0]["available_actions"] == [
        {"action": "continue"},
        {"action": "raise_budget", "cap_key": "daily_cap_tokens", "current_cap": 1000},
    ]
    assert payload["alarms"][0]["session_href"] == f"/sessions/{session['id']}"

    resolved = resolved_auth.json()
    assert resolved["selected_filter"] == "resolved"
    assert len(resolved["alarms"]) == 1
    assert resolved["alarms"][0]["resolved_at"]
    assert resolved["alarms"][0]["resolved_action"] == "continue"
    assert resolved["alarms"][0]["resolved_payload_summary"]
    assert resolved["alarms"][0]["available_actions"] == []

    all_payload = all_auth.json()
    assert all_payload["selected_filter"] == "all"
    assert {alarm["id"] for alarm in all_payload["alarms"]} == {"alarm-open-1", "alarm-resolved-1"}

    filters = payload["filters"]
    assert [f["value"] for f in filters] == ["open", "resolved", "all"]
    assert [f["selected"] for f in filters] == [True, False, False]


def test_react_alarms_resolve_positive_cap_guard_and_json_outcome(tmp_path, monkeypatch):
    """raise_budget rejects non-increasing caps and returns a sanitized JSON outcome."""
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        session = db.create_session(
            database_path,
            task_description="Guard test",
            model="claude-haiku",
            session_key_hash="guard-hash",
            guardrail_overrides={"budget": {"session_cap_tokens": 1000}},
            status="running",
        )
        db.record_alarm(
            database_path,
            session_id=session["id"],
            alarm={
                "id": "alarm-guard-1",
                "type": "SESSION_CAP_EXCEEDED",
                "severity": "HIGH",
                "context": {"session_cap_tokens": 1000, "session_used_tokens": 1000},
                "recommended_action": "Raise session cap.",
            },
        )

        bad = client.post(
            "/alarms/alarm-guard-1/resolve",
            headers={**_portal_headers(), "Accept": "application/json"},
            json={"action": "raise_budget", "payload": {"session_cap_tokens": 500}},
        )
        equal = client.post(
            "/alarms/alarm-guard-1/resolve",
            headers={**_portal_headers(), "Accept": "application/json"},
            json={"action": "raise_budget", "payload": {"session_cap_tokens": 1000}},
        )
        good = client.post(
            "/alarms/alarm-guard-1/resolve",
            headers={**_portal_headers(), "Accept": "application/json"},
            json={"action": "raise_budget", "payload": {"session_cap_tokens": 1001}},
        )

    assert bad.status_code == 200
    assert bad.json()["ok"] is False
    assert bad.json()["alarm"] is None
    assert bad.json()["action"] is None
    assert "strictly greater" in bad.json()["error"]

    assert equal.json()["ok"] is False
    assert good.json()["ok"] is True
    assert good.json()["alarm"]["resolved_at"]
    assert db.get_session(database_path, session["id"])["guardrail_overrides"]["budget"]["session_cap_tokens"] == 1001


def test_react_alarms_resolve_preserves_html_redirect_and_no_auth_json_stays_open(tmp_path, monkeypatch):
    """HTML resolve still redirects; JSON resolve returns the outcome without new auth."""
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        session = db.create_session(
            database_path,
            task_description="Resolve test",
            model="claude-haiku",
            session_key_hash="resolve-hash",
            guardrail_overrides={},
            status="running",
        )
        db.record_alarm(
            database_path,
            session_id=session["id"],
            alarm={
                "id": "alarm-resolve-2",
                "type": "DAILY_CAP_EXCEEDED",
                "severity": "HIGH",
                "context": {"daily_cap_tokens": 100, "daily_used_tokens": 50},
                "recommended_action": "Raise daily cap.",
            },
        )

        html = client.post(
            "/alarms/alarm-resolve-2/resolve",
            headers={**_portal_headers(), "accept": "text/html"},
            data={"action": "continue"},
            follow_redirects=False,
        )
        json = client.post(
            "/alarms/alarm-resolve-2/resolve",
            headers={"Accept": "application/json"},
            json={"action": "continue"},
        )

    assert html.status_code == 303
    assert html.headers["location"] == "/alarms"
    assert json.status_code == 200
    assert json.json()["ok"] is True
    assert json.json()["alarm"]["resolved_at"]


def test_react_alarms_canonical_route_serves_react_when_built(tmp_path, monkeypatch):
    """GET /alarms with a complete build returns the React shell."""
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path) as client:
        response = client.get(
            "/alarms",
            headers={**_portal_headers(), "Accept": "text/html"},
        )
    assert response.status_code == 200
    assert 'id="root"' in response.text


def test_react_alarms_source_contract():
    """Frontend Alarms view matches the backend contract and routing expectations."""
    app_source = Path("frontend/src/App.jsx").read_text(encoding="utf-8")
    shell_source = Path("frontend/src/components/Shell.jsx").read_text(encoding="utf-8")
    source = Path("frontend/src/views/Alarms.jsx").read_text(encoding="utf-8")

    assert 'view: "alarms"' in app_source
    assert '<Alarms />' in app_source
    assert 'to="/alarms"' in shell_source
    assert 'activeView === "alarms"' in shell_source
    api_source = Path("frontend/src/api.js").read_text(encoding="utf-8")

    assert "available_actions" in source
    assert '"/api/alarms?filter="' in source or "`/api/alarms?filter=${" in source
    assert "/alarms/${" in source and "resolve" in source
    assert "postJSON" in source
    assert 'Accept: "application/json"' in api_source
    assert "aria-live" in source
    assert "aria-pressed" in source
    assert "raise_budget" in source
    assert "abort" not in source.lower()
    assert "adjust_guardrail" not in source
