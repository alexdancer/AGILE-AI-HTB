from pathlib import Path

from fastapi.testclient import TestClient

from token_tracker_harness.app import create_app
from token_tracker_harness.settings import Settings


ROOT = Path(__file__).resolve().parents[1]


def test_create_app_health_initializes_database_and_guardrails(tmp_path):
    db_path = tmp_path / "harness.db"
    settings = Settings(database_path=db_path, guardrails_path=ROOT / "guardrails.yaml")

    with TestClient(create_app(settings)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert db_path.exists()
