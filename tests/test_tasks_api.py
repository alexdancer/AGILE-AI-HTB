import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.settings import Settings
from agile_ai_htb.task_launch import refresh_task_from_session


ROOT = Path(__file__).resolve().parents[1]
PORTAL_TOKEN = "test-portal-token"


def _auth_headers():
    return {"Authorization": f"Bearer {PORTAL_TOKEN}"}


def _client(tmp_path):
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    return TestClient(create_app(settings))


class FakeEstimatorLLM:
    def __init__(self, content=None, *, exc=None, usage=None):
        self.content = content or {
            "token_estimate": 12_345,
            "complexity": "modest",
            "recommended_model": "claude-3-5-sonnet-20240620",
            "confidence": 0.82,
            "rationale": "Endpoint plus tests is a modest task.",
            "assumptions": ["No schema migration is needed."],
            "risk_flags": ["integration tests may expand scope"],
            "spike_recommendation": "No spike needed.",
            "budget_note": "Within normal daily budget.",
            "source": "llm",
        }
        self.exc = exc
        self.usage = usage or {"prompt_tokens": 111, "completion_tokens": 22, "total_tokens": 133}
        self.requests = []

    async def acompletion(self, request):
        self.requests.append(request)
        if self.exc:
            raise self.exc
        return {
            "choices": [{"message": {"content": json.dumps(self.content)}}],
            "usage": self.usage,
        }


def _client_with_llm(tmp_path, llm):
    settings = Settings(
        database_path=tmp_path / "harness.db",
        guardrails_path=ROOT / "guardrails.yaml",
        estimator_model="openai/gpt-4.1-mini",
    )
    app = create_app(settings)
    app.state.llm_client = llm
    return TestClient(app)


def test_create_and_update_task_lifecycle(tmp_path):
    with _client(tmp_path) as client:
        created = client.post("/tasks", json={"description": "Add save command"})
        task_id = created.json()["id"]
        updated = client.put(
            f"/tasks/{task_id}",
            json={
                "status": "Ready",
                "estimate_tokens": 12_000,
                "recommended_model": "claude-haiku",
                "description": "Add save command and tests",
            },
        )

    assert created.status_code == 200
    assert created.json()["status"] == "Blocked"
    assert created.json()["metadata"] == {
        "blocked_reason": "Estimate task before launch.",
        "requires_manual_estimate": True,
    }
    assert updated.status_code == 200
    assert updated.json()["id"] == task_id
    assert updated.json()["status"] == "Ready"
    assert updated.json()["estimate_tokens"] == 12_000
    assert updated.json()["recommended_model"] == "claude-haiku"
    assert updated.json()["description"] == "Add save command and tests"


def test_create_task_with_estimate_defaults_to_estimated(tmp_path):
    with _client(tmp_path) as client:
        created = client.post(
            "/tasks",
            json={
                "description": "Add list command",
                "estimate_tokens": 8_000,
                "recommended_model": "claude-haiku",
            },
        )

    assert created.status_code == 200
    assert created.json()["status"] == "Estimated"


def test_create_task_rejects_noncanonical_status_as_blocked(tmp_path):
    with _client(tmp_path) as client:
        created = client.post(
            "/tasks",
            json={"description": "Legacy task", "status": "Backlog"},
        )

    assert created.status_code == 200
    assert created.json()["status"] == "Blocked"
    assert created.json()["metadata"] == {
        "blocked_reason": "Unsupported task status: Backlog",
        "original_status": "Backlog",
    }


def test_create_task_blocks_explicit_estimated_without_estimate(tmp_path):
    with _client(tmp_path) as client:
        created = client.post(
            "/tasks",
            json={"description": "Missing estimate", "status": "Estimated"},
        )

    assert created.status_code == 200
    assert created.json()["status"] == "Blocked"
    assert created.json()["metadata"] == {
        "blocked_reason": "Estimate task before launch.",
        "requires_manual_estimate": True,
        "requested_status": "Estimated",
    }


def test_update_task_rejects_noncanonical_status_as_blocked(tmp_path):
    with _client(tmp_path) as client:
        created = client.post(
            "/tasks",
            json={
                "description": "Estimated task",
                "estimate_tokens": 8_000,
                "recommended_model": "claude-haiku",
            },
        ).json()
        updated = client.put(f"/tasks/{created['id']}", json={"status": "Backlog"})

    assert updated.status_code == 200
    assert updated.json()["status"] == "Blocked"
    assert updated.json()["metadata"] == {
        "blocked_reason": "Unsupported task status: Backlog",
        "original_status": "Backlog",
    }


def test_direct_create_running_is_blocked_and_points_to_launch(tmp_path):
    with _client(tmp_path) as client:
        created = client.post(
            "/tasks",
            json={
                "description": "Cannot directly run",
                "status": "Running",
                "estimate_tokens": 8_000,
                "recommended_model": "claude-haiku",
            },
        )

    assert created.status_code == 200
    assert created.json()["status"] == "Blocked"
    assert created.json()["session_id"] is None
    assert created.json()["metadata"]["blocked_reason"] == "Use launch endpoint to start tasks."


def test_direct_update_done_requires_completed_session(tmp_path):
    with _client(tmp_path) as client:
        created = client.post(
            "/tasks",
            json={
                "description": "Cannot directly finish",
                "estimate_tokens": 8_000,
                "recommended_model": "claude-haiku",
            },
        ).json()
        updated = client.put(f"/tasks/{created['id']}", json={"status": "Done"})

    assert updated.status_code == 200
    assert updated.json()["status"] == "Blocked"
    assert updated.json()["metadata"]["blocked_reason"] == "Use refresh endpoint to finalize completed sessions."


def test_direct_update_done_allows_completed_session_backing(tmp_path):
    with _client(tmp_path) as client:
        session = db.create_session(
            tmp_path / "harness.db",
            task_description="Completed externally",
            model="claude-haiku",
            session_key_hash="f" * 64,
            guardrail_overrides={},
            status="completed",
        )
        created = client.post(
            "/tasks",
            json={
                "description": "Completed externally",
                "estimate_tokens": 8_000,
                "recommended_model": "claude-haiku",
                "session_id": session["id"],
            },
        ).json()
        updated = client.put(f"/tasks/{created['id']}", json={"status": "Done"})

    assert updated.status_code == 200
    assert updated.json()["status"] == "Done"


def test_estimate_uses_llm_structured_json_creates_estimated_task_and_tracks_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM()
    with _client_with_llm(tmp_path, llm) as client:
        response = client.post(
            "/estimate",
            headers=_auth_headers(),
            json={
                "description": "Add an endpoint and tests for sessions",
                "remaining_daily_tokens": 100_000,
                "daily_cap_tokens": 1_000_000,
            },
        )
        task = response.json()
        dashboard = client.get("/dashboard", headers=_auth_headers())
        with db.connect(tmp_path / "harness.db") as conn:
            token_turn = conn.execute("select * from token_turns").fetchone()
            estimation_session = conn.execute("select * from sessions").fetchone()

    assert response.status_code == 200
    assert task["status"] == "Estimated"
    assert task["estimate_tokens"] == 12_345
    assert task["recommended_model"] == "claude-3-5-sonnet-20240620"
    assert task["actual_tokens"] is None
    assert task["metadata"]["estimation_source"] == "llm"
    assert task["metadata"]["confidence"] == 0.82
    assert task["metadata"]["assumptions"] == ["No schema migration is needed."]
    assert task["metadata"]["risk_flags"] == ["integration tests may expand scope"]
    assert task["metadata"]["spike_recommendation"] == "No spike needed."
    assert task["metadata"]["budget_note"] == "Within normal daily budget."
    assert llm.requests[0]["model"] == "openai/gpt-4.1-mini"
    assert "Return ONLY valid JSON" in llm.requests[0]["messages"][0]["content"]
    assert "Add an endpoint and tests for sessions" in llm.requests[0]["messages"][1]["content"]
    assert token_turn["usage_kind"] == "estimation"
    assert token_turn["prompt_tokens"] == 111
    assert token_turn["completion_tokens"] == 22
    assert token_turn["total_tokens"] == 133
    assert estimation_session["status"] == "completed"
    assert estimation_session["session_key_hash"] != "estimation:Add an endpoint and tests for sessions"
    assert len(estimation_session["session_key_hash"]) == 64
    assert all(char in "0123456789abcdef" for char in estimation_session["session_key_hash"])
    assert "133" in dashboard.text


def test_estimate_requires_portal_auth_before_llm_call(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM()
    with _client_with_llm(tmp_path, llm) as client:
        response = client.post("/estimate", json={"description": "Do not spend tokens"})

    assert response.status_code == 401
    assert llm.requests == []


def test_estimate_invalid_llm_result_creates_blocked_manual_task_without_heuristic_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM(content={"complexity": "simple"})
    with _client_with_llm(tmp_path, llm) as client:
        response = client.post("/estimate", headers=_auth_headers(), json={"description": "Fix typo"})

    task = response.json()
    assert response.status_code == 200
    assert task["status"] == "Blocked"
    assert task["estimate_tokens"] is None
    assert task["recommended_model"] is None
    assert task["metadata"]["requires_manual_estimate"] is True
    assert task["metadata"]["estimator_failure_type"] == "EstimatorValidationError"
    assert task["metadata"]["estimation_source"] == "manual_required"


def test_estimate_provider_exception_is_sanitized_and_creates_no_usage_session(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    raw_error = "provider secret outage raw detail"
    llm = FakeEstimatorLLM(exc=RuntimeError(raw_error))
    with _client_with_llm(tmp_path, llm) as client:
        response = client.post(
            "/estimate",
            headers=_auth_headers(),
            json={"description": "Needs provider call"},
        )
        with db.connect(tmp_path / "harness.db") as conn:
            sessions = conn.execute("select * from sessions").fetchall()
            token_turns = conn.execute("select * from token_turns").fetchall()

    task = response.json()
    assert response.status_code == 200
    assert task["status"] == "Blocked"
    assert task["metadata"]["blocked_reason"] == "Estimator unavailable or invalid; manual estimate required."
    assert raw_error not in json.dumps(task)
    assert task["metadata"]["estimator_failure_type"] == "EstimatorUnavailableError"
    assert sessions == []
    assert token_turns == []


def test_estimate_rejects_non_llm_source(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM(content={**FakeEstimatorLLM().content, "source": "heuristic"})
    with _client_with_llm(tmp_path, llm) as client:
        response = client.post("/estimate", headers=_auth_headers(), json={"description": "Fix source"})

    task = response.json()
    assert response.status_code == 200
    assert task["status"] == "Blocked"
    assert task["metadata"]["estimator_failure_type"] == "EstimatorValidationError"


def test_estimate_rejects_unapproved_recommended_model(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM(
        content={**FakeEstimatorLLM().content, "recommended_model": "unapproved-frontier-model"}
    )
    with _client_with_llm(tmp_path, llm) as client:
        response = client.post(
            "/estimate",
            headers=_auth_headers(),
            json={"description": "Reject arbitrary model recommendation"},
        )

    task = response.json()
    assert response.status_code == 200
    assert task["status"] == "Blocked"
    assert task["recommended_model"] is None
    assert task["metadata"]["estimator_failure_type"] == "EstimatorValidationError"


def test_estimate_rejects_bool_numeric_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    for field in ["token_estimate", "confidence"]:
        content = {**FakeEstimatorLLM().content, field: True}
        llm = FakeEstimatorLLM(content=content)
        with _client_with_llm(tmp_path / field, llm) as client:
            response = client.post(
                "/estimate",
                headers=_auth_headers(),
                json={"description": f"Reject bool {field}"},
            )

        task = response.json()
        assert response.status_code == 200
        assert task["status"] == "Blocked"
        assert task["metadata"]["estimator_failure_type"] == "EstimatorValidationError"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"estimate_tokens": True, "recommended_model": "claude-haiku"}, "estimate_tokens"),
        ({"estimate_tokens": -1, "recommended_model": "claude-haiku"}, "estimate_tokens"),
        ({"actual_tokens": True}, "actual_tokens"),
        ({"actual_tokens": -1}, "actual_tokens"),
    ],
)
def test_create_task_rejects_bool_and_negative_numeric_fields(tmp_path, payload, field):
    with _client(tmp_path) as client:
        response = client.post("/tasks", json={"description": "Bad numeric", **payload})

    assert response.status_code == 422
    assert field in response.text


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"estimate_tokens": True}, "estimate_tokens"),
        ({"estimate_tokens": -1}, "estimate_tokens"),
        ({"actual_tokens": True}, "actual_tokens"),
        ({"actual_tokens": -1}, "actual_tokens"),
    ],
)
def test_update_task_rejects_bool_and_negative_numeric_fields(tmp_path, payload, field):
    with _client(tmp_path) as client:
        created = client.post("/tasks", json={"description": "Bad numeric update"}).json()
        response = client.put(f"/tasks/{created['id']}", json=payload)

    assert response.status_code == 422
    assert field in response.text


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"remaining_daily_tokens": True}, "remaining_daily_tokens"),
        ({"remaining_daily_tokens": -1}, "remaining_daily_tokens"),
        ({"daily_cap_tokens": True}, "daily_cap_tokens"),
        ({"daily_cap_tokens": -1}, "daily_cap_tokens"),
    ],
)
def test_estimate_rejects_bool_and_negative_numeric_request_fields(
    tmp_path, monkeypatch, payload, field
):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM()
    with _client_with_llm(tmp_path, llm) as client:
        response = client.post(
            "/estimate",
            headers=_auth_headers(),
            json={"description": "Bad estimate request numeric", **payload},
        )

    assert response.status_code == 422
    assert field in response.text
    assert llm.requests == []


def test_manual_update_with_estimate_marks_estimation_source_manual(tmp_path):
    with _client(tmp_path) as client:
        created = client.post("/tasks", json={"description": "Needs manual estimate"}).json()
        updated = client.put(
            f"/tasks/{created['id']}",
            json={"estimate_tokens": 9000, "recommended_model": "claude-haiku"},
        )

    assert updated.status_code == 200
    assert updated.json()["metadata"]["estimation_source"] == "manual"


def test_manual_update_after_estimator_failure_marks_estimation_source_manual(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM(content={"complexity": "simple"})
    with _client_with_llm(tmp_path, llm) as client:
        created = client.post("/estimate", headers=_auth_headers(), json={"description": "Fix typo"})
        task = created.json()
        updated = client.put(
            f"/tasks/{task['id']}",
            json={"estimate_tokens": 9000, "recommended_model": "claude-haiku"},
        )

    assert created.status_code == 200
    assert task["status"] == "Blocked"
    assert task["metadata"]["estimation_source"] == "manual_required"
    assert updated.status_code == 200
    assert updated.json()["estimate_tokens"] == 9000
    assert updated.json()["recommended_model"] == "claude-haiku"
    assert updated.json()["metadata"]["estimation_source"] == "manual"


def test_update_missing_task_returns_404(tmp_path):
    with _client(tmp_path) as client:
        response = client.put("/tasks/missing", json={"status": "Done"})

    assert response.status_code == 404


def test_launch_blocks_unverified_adapter_without_session_or_runner(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []
    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = runner_calls.append
        task = client.post(
            "/tasks",
            json={
                "description": "Launch only after token proof",
                "estimate_tokens": 8000,
                "recommended_model": "gpt-5.1-codex",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.1-codex"],
            is_default=True,
        )

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "proxy_url": "http://127.0.0.1:8000/v1"},
        )
        board = client.get("/board", headers=_auth_headers())
        with db.connect(tmp_path / "harness.db") as conn:
            sessions = conn.execute("select * from sessions").fetchall()

    assert response.status_code == 409
    body = response.json()
    assert body["task"]["status"] == "Estimated"
    assert body["task"]["session_id"] is None
    assert "Token tracking has not been verified" in body["launch_guardrails"]["reasons"][0]
    assert body["task"]["metadata"]["launch_blocked_reason"] == "Token tracking has not been verified for this adapter."
    assert runner_calls == []
    assert sessions == []
    assert "Token tracking has not been verified for this adapter." in board.text


def test_launch_verified_adapter_creates_running_session_and_redacts_raw_session_key(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        return {"returncode": 0, "stdout": "started", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post(
            "/tasks",
            json={
                "description": "Implement launch button",
                "estimate_tokens": 8000,
                "recommended_model": "gpt-5.1-codex",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"launch_template": ["codex", "--model", "{model}", "--prompt", "{prompt}"]},
            supported_models=["gpt-5.1-codex"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "proxy_url": "http://127.0.0.1:8000/v1"},
        )
        launched = response.json()["task"]
        board = client.get("/board", headers=_auth_headers())
        artifact = client.get(f"/session/{launched['session_id']}/artifact", headers=_auth_headers()).json()

    assert response.status_code == 200
    assert launched["status"] == "Running"
    assert launched["session_id"].startswith("sess_")
    assert len(runner_calls) == 1
    assert runner_calls[0].env["OPENAI_API_KEY"].startswith("sk_sess_")
    assert runner_calls[0].env["AGILE_AI_HTB_SESSION_API_KEY"].startswith("sk_sess_")
    serialized = json.dumps({"response": response.json(), "board": board.text, "artifact": artifact})
    assert "sk_sess_" not in serialized
    assert "Session report" in board.text
    assert f"/sessions/{launched['session_id']}" in board.text
    assert artifact["session"]["session_key_hash"] != runner_calls[0].env["OPENAI_API_KEY"]


def test_launch_sanitizes_runner_output_everywhere(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    leaked_key = "sk_sess_FAKESECRET2099"

    def fake_runner(plan):
        return {
            "returncode": 0,
            "stdout": f"started with {leaked_key}",
            "stderr": f"warning includes {leaked_key}",
        }

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post(
            "/tasks",
            json={
                "description": "Do not leak runner output secrets",
                "estimate_tokens": 8000,
                "recommended_model": "gpt-5.1-codex",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.1-codex"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "proxy_url": "http://127.0.0.1:8000/v1"},
        )
        launched = response.json()["task"]
        board = client.get("/board", headers=_auth_headers())
        artifact = client.get(f"/session/{launched['session_id']}/artifact", headers=_auth_headers()).json()
        with db.connect(tmp_path / "harness.db") as conn:
            metadata_json = conn.execute("select metadata_json from tasks where id = ?", (task["id"],)).fetchone()[0]

    serialized = json.dumps(
        {"response": response.json(), "board": board.text, "artifact": artifact, "metadata_json": metadata_json}
    )
    assert response.status_code == 200
    assert leaked_key not in serialized
    assert "FAKESECRET2099" not in serialized
    assert "***REDACTED***" in serialized


def test_board_form_launch_uses_default_proxy_for_verified_default_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        return {"returncode": 0, "stdout": "started", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post(
            "/tasks",
            json={
                "description": "Launch from board form",
                "estimate_tokens": 8000,
                "recommended_model": "gpt-5.1-codex",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"launch_template": ["codex", "--model", "{model}"]},
            supported_models=["gpt-5.1-codex"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers={**_auth_headers(), "accept": "text/html"},
            data={},
            follow_redirects=False,
        )
        refreshed = db.get_task(tmp_path / "harness.db", task["id"])

    assert response.status_code == 303
    assert response.headers["location"] == "/board"
    assert refreshed["status"] == "Running"
    assert len(runner_calls) == 1
    assert runner_calls[0].env["OPENAI_BASE_URL"] == "http://127.0.0.1:8000/v1"
    assert "sk_sess_" not in response.text


def test_launch_accepts_manual_estimate_payload_before_guardrails(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        return {"returncode": 0, "stdout": "started", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post("/tasks", json={"description": "Unestimated launch"}).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.1-codex"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.1-codex", "estimate_tokens": 9000},
        )

    body = response.json()
    assert response.status_code == 200
    assert body["task"]["status"] == "Running"
    assert body["task"]["estimate_tokens"] == 9000
    assert body["task"]["recommended_model"] == "gpt-5.1-codex"
    assert body["task"]["metadata"]["estimation_source"] == "manual"
    assert runner_calls[0].env["OPENAI_BASE_URL"] == "http://127.0.0.1:8000/v1"


def test_launch_done_with_manual_estimate_payload_stays_done_without_session_or_runner(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []
    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = runner_calls.append
        task = db.create_task(
            tmp_path / "harness.db",
            description="Already done",
            status="Done",
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
        )
        before_sessions = len(db.list_sessions(tmp_path / "harness.db"))

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.1-codex", "estimate_tokens": 9000},
        )
        after = db.get_task(tmp_path / "harness.db", task["id"])

    assert response.status_code == 409
    assert after["status"] == "Done"
    assert after["estimate_tokens"] == 8000
    assert after["recommended_model"] == "gpt-5.1-codex"
    assert len(db.list_sessions(tmp_path / "harness.db")) == before_sessions
    assert runner_calls == []


def test_launch_second_call_after_running_claim_is_rejected_without_second_runner(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        return {"returncode": 0, "stdout": "started", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post(
            "/tasks",
            json={
                "description": "Launch once only",
                "estimate_tokens": 8000,
                "recommended_model": "gpt-5.1-codex",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.1-codex"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        first = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "proxy_url": "http://127.0.0.1:8000/v1"},
        )
        second = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "proxy_url": "http://127.0.0.1:8000/v1"},
        )

    assert first.status_code == 200
    assert second.status_code == 409
    assert len(runner_calls) == 1


@pytest.mark.parametrize("estimate_tokens", [True, 0, -1])
def test_launch_rejects_invalid_manual_estimate_tokens(tmp_path, monkeypatch, estimate_tokens):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        task = client.post("/tasks", json={"description": "Bad launch estimate"}).json()
        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"model": "gpt-5.1-codex", "estimate_tokens": estimate_tokens},
        )

    assert response.status_code == 422
    assert "estimate_tokens" in response.text


@pytest.mark.parametrize("status", ["Blocked", "Done", "Review", "Running"])
def test_launch_is_status_gated_without_session_or_runner(tmp_path, monkeypatch, status):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []
    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = runner_calls.append
        session_id = None
        if status == "Running":
            session_id = db.create_session(
                tmp_path / "harness.db",
                task_description="Already running",
                model="gpt-5.1-codex",
                session_key_hash="d" * 64,
                guardrail_overrides={},
                status="running",
            )["id"]
        task = db.create_task(
            tmp_path / "harness.db",
            description=f"{status} task",
            status=status,
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
            session_id=session_id,
        )
        before_sessions = len(db.list_sessions(tmp_path / "harness.db"))
        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.1-codex"},
        )
        after = db.get_task(tmp_path / "harness.db", task["id"])

    assert response.status_code == 409
    assert after["status"] == status
    assert len(db.list_sessions(tmp_path / "harness.db")) == before_sessions
    assert runner_calls == []
    assert "Only Estimated or Ready tasks can launch." in after["metadata"].get("launch_blocked_reason", "")


def test_refresh_task_endpoint_updates_running_task_from_session(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        session = db.create_session(
            tmp_path / "harness.db",
            task_description="Refresh endpoint done",
            model="claude-haiku",
            session_key_hash="e" * 64,
            guardrail_overrides={},
            status="completed",
        )
        task = db.create_task(
            tmp_path / "harness.db",
            description="Refresh endpoint done",
            status="Running",
            estimate_tokens=1000,
            recommended_model="claude-haiku",
            session_id=session["id"],
        )

        response = client.post(f"/tasks/{task['id']}/refresh", headers=_auth_headers())

    assert response.status_code == 200
    assert response.json()["status"] == "Done"


def test_fake_worker_token_row_after_launch_appears_in_session_report(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    def fake_runner(plan):
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=plan.metadata["session_id"],
            usage_kind="worker",
            model=plan.metadata["model"],
            prompt_tokens=123,
            completion_tokens=45,
            cost=0.02,
            raw_usage={"total_tokens": 168, "proof": "fake-worker-token-proof"},
        )
        return {"returncode": 0, "stdout": "started", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post(
            "/tasks",
            json={"description": "Record worker tokens", "estimate_tokens": 8000, "recommended_model": "gpt-5.1-codex"},
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.1-codex"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})
        launched = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "proxy_url": "http://127.0.0.1:8000/v1"},
        ).json()["task"]
        report = client.get(f"/sessions/{launched['session_id']}", headers=_auth_headers())
        artifact = client.get(f"/session/{launched['session_id']}/artifact", headers=_auth_headers()).json()

    assert artifact["token_log"][0]["usage_kind"] == "worker"
    assert artifact["token_log"][0]["total_tokens"] == 168
    assert report.status_code == 200
    assert "168" in report.text
    assert "worker" in report.text


def test_refresh_task_from_session_maps_completion_to_done_review_or_blocked(tmp_path):
    database_path = tmp_path / "harness.db"
    db.init_db(database_path)
    clean_session = db.create_session(
        database_path,
        task_description="Clean done",
        model="claude-haiku",
        session_key_hash="a" * 64,
        guardrail_overrides={},
        status="running",
    )
    clean_task = db.create_task(
        database_path,
        description="Clean done",
        status="Running",
        estimate_tokens=1000,
        recommended_model="claude-haiku",
        session_id=clean_session["id"],
    )
    db.update_session_status(database_path, clean_session["id"], "completed")
    assert refresh_task_from_session(database_path, clean_task["id"])["status"] == "Done"

    review_session = db.create_session(
        database_path,
        task_description="Needs review",
        model="claude-haiku",
        session_key_hash="b" * 64,
        guardrail_overrides={},
        status="completed",
    )
    review_task = db.create_task(
        database_path,
        description="Needs review",
        status="Running",
        estimate_tokens=1000,
        recommended_model="claude-haiku",
        session_id=review_session["id"],
    )
    db.record_checkpoint_result(
        database_path,
        session_id=review_session["id"],
        checkpoint={"name": "quality", "passed": False, "details": {}},
    )
    assert refresh_task_from_session(database_path, review_task["id"])["status"] == "Review"

    failed_session = db.create_session(
        database_path,
        task_description="Failed launch",
        model="claude-haiku",
        session_key_hash="c" * 64,
        guardrail_overrides={},
        status="failed",
    )
    failed_task = db.create_task(
        database_path,
        description="Failed launch",
        status="Running",
        estimate_tokens=1000,
        recommended_model="claude-haiku",
        session_id=failed_session["id"],
    )
    assert refresh_task_from_session(database_path, failed_task["id"])["status"] == "Blocked"
