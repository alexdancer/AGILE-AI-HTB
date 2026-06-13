import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.settings import Settings
from agile_ai_htb.worker_adapters import SENTINEL_RESPONSE, verify_worker_adapter

ROOT = Path(__file__).resolve().parents[1]
PORTAL_TOKEN = "test-portal-token"


def _auth_headers():
    return {"Authorization": f"Bearer {PORTAL_TOKEN}"}


def _client(tmp_path):
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    return TestClient(create_app(settings))


class FakeRunner:
    def __init__(self, stdout=SENTINEL_RESPONSE, returncode=0):
        self.stdout = stdout
        self.returncode = returncode
        self.calls = []

    def __call__(self, plan):
        self.calls.append(plan)
        return {"returncode": self.returncode, "stdout": self.stdout, "stderr": ""}


def test_verify_worker_adapter_uses_fake_runner_sentinel_and_requires_token_row(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(tmp_path),
        config={"verification_template": ["opencode", "run", "{prompt}"]},
        supported_models=["opencode/gpt-5.1"],
    )
    runner = FakeRunner()

    result = verify_worker_adapter(
        db_path,
        "opencode",
        model="opencode/gpt-5.1",
        proxy_url="http://127.0.0.1:8000/v1",
        runner=runner,
        token_recorder=lambda session_id: db.record_token_turn(
            db_path,
            session_id=session_id,
            usage_kind="adapter_verification",
            model="opencode/gpt-5.1",
            prompt_tokens=5,
            completion_tokens=1,
            cost=0,
            raw_usage={"total_tokens": 6},
        ),
    )

    adapter = db.get_worker_adapter(db_path, "opencode")
    session = db.get_session(db_path, result.session_id)
    artifact = db.build_session_artifact(db_path, result.session_id)
    assert result.passed is True
    assert session["status"] == "completed"
    assert adapter["verification_status"] == "verified"
    assert adapter["verification_evidence"]["sentinel_matched"] is True
    assert artifact["token_log"][0]["usage_kind"] == "adapter_verification"
    assert artifact["token_log"][0]["model"] == "opencode/gpt-5.1"
    assert len(runner.calls) == 1
    assert runner.calls[0].env["AGILE_AI_HTB_SESSION_API_KEY"].startswith("sk_sess_")
    assert runner.calls[0].env["OPENAI_BASE_URL"] == "http://127.0.0.1:8000/v1"
    assert runner.calls[0].env["OPENAI_API_KEY"] == runner.calls[0].env["AGILE_AI_HTB_SESSION_API_KEY"]
    assert runner.calls[0].command == ["opencode", "run", "Reply exactly AGILE_AI_HTB_ADAPTER_OK"]
    assert runner.calls[0].cwd == tmp_path
    assert "sk_sess_" not in str(adapter["verification_evidence"])


def test_verify_worker_adapter_fails_when_token_row_missing_even_if_sentinel_matches(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "codex",
        workdir=str(tmp_path),
        config={"verification_template": ["codex", "--prompt", "{prompt}"]},
        supported_models=["gpt-5.1-codex"],
    )

    result = verify_worker_adapter(
        db_path,
        "codex",
        model="gpt-5.1-codex",
        proxy_url="http://127.0.0.1:8000/v1",
        runner=FakeRunner(),
    )

    adapter = db.get_worker_adapter(db_path, "codex")
    session = db.get_session(db_path, result.session_id)
    assert result.passed is False
    assert session["status"] == "failed"
    assert "No adapter_verification token row was recorded for selected model." in result.reasons
    assert adapter["verification_status"] == "failed"
    assert adapter["verification_evidence"]["sentinel_matched"] is True


def test_verify_worker_adapter_fails_for_wrong_sentinel_without_real_cli(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "claude_code",
        workdir=str(tmp_path),
        config={"verification_template": ["claude", "-p", "{prompt}"]},
        supported_models=["claude-3-5-sonnet-latest"],
    )

    result = verify_worker_adapter(
        db_path,
        "claude_code",
        model="claude-3-5-sonnet-latest",
        proxy_url="http://127.0.0.1:8000/v1",
        runner=FakeRunner(stdout="not ok"),
        token_recorder=lambda session_id: db.record_token_turn(
            db_path,
            session_id=session_id,
            usage_kind="adapter_verification",
            model="claude-3-5-sonnet-latest",
            prompt_tokens=5,
            completion_tokens=1,
            cost=0,
            raw_usage={"total_tokens": 6},
        ),
    )

    assert result.passed is False
    assert "Adapter did not return exact verification sentinel." in result.reasons


def test_verify_worker_adapter_fails_fast_without_runner_when_model_unsupported(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "codex",
        workdir=str(tmp_path),
        config={"verification_template": ["codex", "--prompt", "{prompt}"]},
        supported_models=["gpt-5.1-codex"],
    )
    runner = FakeRunner()

    result = verify_worker_adapter(
        db_path,
        "codex",
        model="unsupported-model",
        proxy_url="http://127.0.0.1:8000/v1",
        runner=runner,
    )

    adapter = db.get_worker_adapter(db_path, "codex")
    session = db.get_session(db_path, result.session_id)
    assert result.passed is False
    assert session["status"] == "failed"
    assert "Selected model is not supported by this adapter." in result.reasons
    assert runner.calls == []
    assert adapter["verification_status"] == "failed"
    assert adapter["verification_evidence"]["preflight_failed"] is True


def test_verify_worker_adapter_marks_failed_evidence_when_cli_is_missing(tmp_path, monkeypatch):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "codex",
        workdir=str(tmp_path),
        config={"verification_template": ["missing-codex", "--api-key", "abc123", "--prompt", "{prompt}"]},
        supported_models=["gpt-5.1-codex"],
    )

    def fake_run(*args, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", args[0][0])

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = verify_worker_adapter(
        db_path,
        "codex",
        model="gpt-5.1-codex",
        proxy_url="http://127.0.0.1:8000/v1",
    )

    adapter = db.get_worker_adapter(db_path, "codex")
    session = db.get_session(db_path, result.session_id)
    serialized = str(adapter["verification_evidence"])
    assert result.passed is False
    assert "Adapter verification command failed." in result.reasons
    assert adapter["verification_status"] == "failed"
    assert session["status"] == "failed"
    assert adapter["verification_evidence"]["returncode"] != 0
    assert "Failed to launch command" in adapter["verification_evidence"]["stderr"]
    assert "abc123" not in serialized


def test_verify_worker_adapter_returns_sanitized_evidence(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(tmp_path),
        config={"verification_template": ["opencode", "--api-key", "secret-value", "{prompt}"]},
        supported_models=["opencode/gpt-5.1"],
    )

    result = verify_worker_adapter(
        db_path,
        "opencode",
        model="opencode/gpt-5.1",
        proxy_url="http://127.0.0.1:8000/v1",
        runner=FakeRunner(stdout="secret-output"),
    )

    stored = db.get_worker_adapter(db_path, "opencode")["verification_evidence"]
    assert result.evidence == stored
    serialized = str(result.evidence)
    assert "secret" not in serialized
    assert "sk_sess_" not in serialized
    assert "***REDACTED***" in serialized


def test_worker_adapter_verify_route_requires_auth_uses_injected_runner_and_token_recorder(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner = FakeRunner()
    recorded_sessions = []

    def token_recorder(session_id):
        recorded_sessions.append(session_id)
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=session_id,
            usage_kind="adapter_verification",
            model="gpt-5.1-codex",
            prompt_tokens=5,
            completion_tokens=1,
            cost=0,
            raw_usage={"total_tokens": 6, "api_key": "sk_ses_fake_leak"},
        )

    with _client(tmp_path) as client:
        client.app.state.worker_adapter_verification_runner = runner
        client.app.state.worker_adapter_verification_token_recorder = token_recorder
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"verification_template": ["codex", "--prompt", "{prompt}"]},
            supported_models=["gpt-5.1-codex"],
        )

        unauthorized = client.post(
            "/settings/workers/codex/verify",
            json={"model": "gpt-5.1-codex", "proxy_url": "http://127.0.0.1:8000/v1"},
        )
        response = client.post(
            "/settings/workers/codex/verify",
            headers=_auth_headers(),
            json={"model": "gpt-5.1-codex", "proxy_url": "http://127.0.0.1:8000/v1"},
        )

    body = response.json()
    serialized = str(body)
    assert unauthorized.status_code == 401
    assert response.status_code == 200
    assert body["passed"] is True
    assert body["adapter_id"] == "codex"
    assert len(runner.calls) == 1
    assert len(recorded_sessions) == 1
    assert "sk_sess_" not in serialized
    assert "sk_ses_fake_leak" not in serialized


def test_workers_page_renders_verify_form_without_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "opencode",
            workdir=str(tmp_path),
            config={"env": {"OPENAI_API_KEY": "super-secret-key"}},
            supported_models=["opencode/gpt-5.1"],
        )

        response = client.get("/settings/workers", headers=_auth_headers())

    assert response.status_code == 200
    assert 'action="/settings/workers/opencode/verify"' in response.text
    assert 'name="model"' in response.text
    assert 'name="proxy_url"' in response.text
    assert "http://127.0.0.1:8000/v1" in response.text
    assert "super-secret-key" not in response.text
    assert "sk_sess_" not in response.text
