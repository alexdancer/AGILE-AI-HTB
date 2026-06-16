from pathlib import Path

from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.settings import Settings

ROOT = Path(__file__).resolve().parents[1]
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
    assert "htb serve --local-runner" in response.json()["detail"]


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
    assert "Connected project" in html
    assert "portal-project" in html
    assert str(root.resolve()) in html
    assert "Analysis-ready" in html
    assert "pytest" in html
    assert "fastapi" in html
    assert "README.md" in html



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
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "opencode", verified=True, evidence={"ok": True})
        response = client.post(f"/settings/project/{project['id']}/read-only-proof", headers=_headers())

    body = response.json()
    assert response.status_code == 200
    assert body["task"]["status"] == "Running"
    assert body["task"]["metadata"]["read_only_proof"] is True
    assert body["task"]["metadata"]["session_report"]["test_command"] == "pytest"
    assert runner_calls[0].cwd == root.resolve()
