from pathlib import Path

from fastapi.testclient import TestClient

from agile_ai_htb.app import create_app
from agile_ai_htb.settings import Settings


ROOT = Path(__file__).resolve().parents[1]


def _client(tmp_path):
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    return TestClient(create_app(settings))


def test_create_and_update_task_lifecycle(tmp_path):
    with _client(tmp_path) as client:
        created = client.post("/tasks", json={"description": "Add save command"})
        task_id = created.json()["id"]
        updated = client.put(
            f"/tasks/{task_id}",
            json={
                "status": "In Progress",
                "estimate_tokens": 12_000,
                "recommended_model": "claude-haiku",
                "description": "Add save command and tests",
            },
        )

    assert created.status_code == 200
    assert created.json()["status"] == "Backlog"
    assert updated.status_code == 200
    assert updated.json()["id"] == task_id
    assert updated.json()["status"] == "In Progress"
    assert updated.json()["estimate_tokens"] == 12_000
    assert updated.json()["recommended_model"] == "claude-haiku"
    assert updated.json()["description"] == "Add save command and tests"


def test_estimate_classifies_easy_modest_and_complex_with_budget_downgrade(tmp_path):
    with _client(tmp_path) as client:
        easy = client.post("/estimate", json={"description": "Fix typo"}).json()
        modest = client.post("/estimate", json={"description": "Add an endpoint and tests for sessions"}).json()
        complex_response = client.post(
            "/estimate",
            json={
                "description": "Design a new architecture for authentication, database migrations, and streaming proxy integration",
                "remaining_daily_tokens": 100_000,
                "daily_cap_tokens": 1_000_000,
            },
        )

    complex_body = complex_response.json()
    assert easy["complexity"] == "simple"
    assert easy["recommended_model"] == "claude-haiku"
    assert modest["complexity"] == "modest"
    assert modest["recommended_model"] == "claude-sonnet"
    assert complex_response.status_code == 200
    assert complex_body["complexity"] == "complex"
    assert complex_body["token_estimate"] > modest["token_estimate"]
    assert complex_body["recommended_model"] == "claude-sonnet"
    assert "Budget is tight" in complex_body["budget_note"]


def test_update_missing_task_returns_404(tmp_path):
    with _client(tmp_path) as client:
        response = client.put("/tasks/missing", json={"status": "Done"})

    assert response.status_code == 404
