import os
from pathlib import Path

from fastapi.testclient import TestClient

from foreman_ai_hq.app import create_app
from foreman_ai_hq.settings import Settings


ROOT = Path(__file__).resolve().parents[2]


def test_create_app_health_initializes_database_and_guardrails(tmp_path):
    db_path = tmp_path / "harness.db"
    settings = Settings(database_path=db_path, guardrails_path=ROOT / "guardrails.yaml")

    with TestClient(create_app(settings)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert db_path.exists()


def test_create_app_does_not_fan_out_control_plane_key_to_provider_envs(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTROL_TEST_KEY", "test-key")
    for env_name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "COHERE_API_KEY", "GROQ_API_KEY"]:
        monkeypatch.delenv(env_name, raising=False)
    settings = Settings(
        database_path=tmp_path / "harness.db",
        guardrails_path=ROOT / "guardrails.yaml",
        control_plane_api_key_env="CONTROL_TEST_KEY",
    )

    with TestClient(create_app(settings)) as client:
        assert client.get("/health").status_code == 200

    for env_name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "COHERE_API_KEY", "GROQ_API_KEY"]:
        assert env_name not in os.environ
