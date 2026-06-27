import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.project_context import project_task_metadata
from agile_ai_htb.settings import Settings
from agile_ai_htb.task_launch import refresh_task_from_session


ROOT = Path(__file__).resolve().parents[2]
PORTAL_TOKEN = "test-portal-token"


def _auth_headers():
    return {"Authorization": f"Bearer {PORTAL_TOKEN}"}


def _wait_for_worker_run(db_path: Path, task_id: str, status: str | None = None):
    deadline = time.time() + 2
    while time.time() < deadline:
        runs = db.list_worker_runs(db_path, task_id=task_id)
        if runs and (status is None or runs[-1]["status"] == status):
            return runs[-1]
        time.sleep(0.01)
    raise AssertionError("worker run did not reach expected status")


def _client(tmp_path):
    settings = Settings(database_path=tmp_path / "harness.db", guardrails_path=ROOT / "guardrails.yaml")
    db.init_db(settings.database_path)
    app = create_app(settings)
    project_root = tmp_path / "connected-project"
    project_root.mkdir(exist_ok=True)
    db.upsert_connected_project(
        settings.database_path,
        name=project_root.name,
        root_path=str(project_root.resolve()),
        profile={"name": project_root.name, "root_path": str(project_root.resolve()), "test_command": "pytest"},
        capability={"state": "launch_ready", "can_launch": True},
    )
    return TestClient(app)




class FakeSequentialLLM:
    def __init__(self, contents):
        self.contents = list(contents)
        self.requests = []
        self.usage = {"prompt_tokens": 111, "completion_tokens": 22, "total_tokens": 133}

    async def acompletion(self, request):
        self.requests.append(request)
        if not self.contents:
            raise AssertionError("unexpected LLM request")
        return {
            "choices": [{"message": {"content": json.dumps(self.contents.pop(0))}}],
            "usage": self.usage,
        }


def _breakdown_content(*titles):
    candidates = [
        {
            "kind": "implementation",
            "title": title,
            "prompt": f"Implement {title}",
            "acceptance_criteria": f"{title} is covered by tests.",
            "constraints": [],
            "human_in_loop": True,
        }
        for title in titles
    ]
    return {
        "decision": "proposed_task_breakdown" if len(candidates) > 1 else "single_task",
        "candidates": candidates,
        "rejected_items": [
            {"text": "Do not add network dependencies.", "reason": "constraint, not a task"}
        ],
        "global_contract_summary": "Accepted slices must preserve the DEMO_TASK_2099 contract end-to-end.",
        "global_constraints": ["Do not add network dependencies."],
        "verification": ["Run pytest."],
        "non_goals": [],
        "recommended_sequence": list(titles),
        "confidence": 0.86,
        "rationale": "Markdown contains multiple vertical slices plus constraints.",
        "source": "llm",
    }


def _integrated_artifact_breakdown():
    return {
        "decision": "proposed_task_breakdown",
        "candidates": [
            {
                "kind": "implementation",
                "title": "Build DEMO_CLI_2099 parser",
                "prompt": "Implement the parser slice for DEMO_CLI_2099.",
                "acceptance_criteria": "Parser tests pass.",
                "constraints": ["Preserve DEMO_ID_999 values."],
                "human_in_loop": True,
            },
            {
                "kind": "implementation",
                "title": "Render DEMO_REPORT_2099 output",
                "prompt": "Implement the report rendering slice for DEMO_REPORT_2099.",
                "acceptance_criteria": "Report shape is covered.",
                "constraints": [],
                "human_in_loop": True,
            },
            {
                "kind": "acceptance_verification",
                "title": "Acceptance Verification for DEMO_CLI_2099",
                "prompt": "Verify the combined CLI/report artifact against the source contract.",
                "acceptance_criteria": "Executable smoke proof and findings are recorded.",
                "constraints": ["Do not rebuild the CLI."],
                "human_in_loop": True,
            },
        ],
        "rejected_items": [],
        "global_contract_summary": "DEMO_CLI_2099 must parse input and emit DEMO_REPORT_2099 with 999-style IDs.",
        "global_constraints": ["Use only synthetic DEMO_2099 data."],
        "verification": ["Run a CLI smoke check."],
        "non_goals": [],
        "recommended_sequence": [
            "Build DEMO_CLI_2099 parser",
            "Render DEMO_REPORT_2099 output",
            "Acceptance Verification for DEMO_CLI_2099",
        ],
        "confidence": 0.9,
        "rationale": "Two implementation slices create one integrated artifact requiring final proof.",
        "source": "llm",
    }


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
    db.init_db(settings.database_path)
    app.state.llm_client = llm
    project_root = tmp_path / "connected-project"
    project_root.mkdir(exist_ok=True)
    db.upsert_connected_project(
        settings.database_path,
        name=project_root.name,
        root_path=str(project_root.resolve()),
        profile={"name": project_root.name, "root_path": str(project_root.resolve()), "test_command": "pytest"},
        capability={"state": "launch_ready", "can_launch": True},
    )
    return TestClient(app)

def test_review_action_save_prompt_and_mark_done_preserve_completed_session_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        session = db.create_session(
            database_path,
            task_description="Reviewable work",
            model="gpt-5.1-codex",
            session_key_hash="r" * 64,
            guardrail_overrides={},
            status="completed",
        )
        task = db.create_task(
            database_path,
            description="Reviewable work",
            status="Review",
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
            actual_tokens=321,
            session_id=session["id"],
        )

        saved = client.post(
            f"/tasks/{task['id']}/review",
            headers=_auth_headers(),
            json={"action": "save_prompt", "review_prompt": "Focus on DEMO review note 2099."},
        )
        done = client.post(
            f"/tasks/{task['id']}/review",
            headers=_auth_headers(),
            json={"action": "mark_done"},
        )

    assert saved.status_code == 200
    assert saved.json()["status"] == "Review"
    assert saved.json()["metadata"]["review_prompt"] == "Focus on DEMO review note 2099."
    assert done.status_code == 200
    body = done.json()
    assert body["status"] == "Done"
    assert body["session_id"] == session["id"]
    assert body["actual_tokens"] == 321
    assert body["metadata"]["review_decision"] == "accepted"
    assert body["metadata"]["reviewed_by"] == "operator"

def test_review_action_block_requires_reason_and_records_operator_decision(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        session = db.create_session(
            database_path,
            task_description="Blockable review",
            model="gpt-5.1-codex",
            session_key_hash="s" * 64,
            guardrail_overrides={},
            status="completed",
        )
        task = db.create_task(
            database_path,
            description="Blockable review",
            status="Review",
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
            session_id=session["id"],
        )

        missing_reason = client.post(
            f"/tasks/{task['id']}/review",
            headers=_auth_headers(),
            json={"action": "block"},
        )
        blocked = client.post(
            f"/tasks/{task['id']}/review",
            headers=_auth_headers(),
            json={"action": "block", "blocked_reason": "DEMO blocker reason 2099."},
        )

    assert missing_reason.status_code == 409
    assert blocked.status_code == 200
    body = blocked.json()
    assert body["status"] == "Blocked"
    assert body["metadata"]["review_decision"] == "blocked"
    assert body["metadata"]["blocked_reason"] == "DEMO blocker reason 2099."
    assert body["session_id"] == session["id"]

def test_review_action_agent_review_uses_control_plane_and_stays_in_review(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM(
        content={
            "summary": "DEMO review says the task is acceptable.",
            "recommendation": "approve",
            "findings": [{"severity": "low", "message": "DEMO finding only."}],
        },
        usage={"prompt_tokens": 40, "completion_tokens": 9, "total_tokens": 49},
    )
    database_path = tmp_path / "harness.db"
    with _client_with_llm(tmp_path, llm) as client:
        session = db.create_session(
            database_path,
            task_description="Agent reviewed work",
            model="gpt-5.1-codex",
            session_key_hash="t" * 64,
            guardrail_overrides={},
            status="completed",
        )
        db.record_token_turn(
            database_path,
            session_id=session["id"],
            usage_kind="worker",
            model="gpt-5.1-codex",
            prompt_tokens=111,
            completion_tokens=22,
            cost=0,
            raw_usage={"total_tokens": 133},
        )
        task = db.create_task(
            database_path,
            description="Agent reviewed work",
            status="Review",
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
            session_id=session["id"],
            metadata={"launch_stdout": "DEMO worker stdout 2099 with password=bad"},
        )

        response = client.post(
            f"/tasks/{task['id']}/review",
            headers=_auth_headers(),
            json={"action": "agent_review", "review_prompt": "Check DEMO edge case 2099."},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Review"
    assert body["metadata"]["review_prompt"] == "Check DEMO edge case 2099."
    review = body["metadata"]["agent_review"]
    assert review["status"] == "completed"
    assert review["summary"] == "DEMO review says the task is acceptable."
    assert review["recommendation"] == "approve"
    assert review["findings"][0]["message"] == "DEMO finding only."
    assert review["review_session_id"] != session["id"]
    assert llm.requests
    review_context = llm.requests[0]["messages"][1]["content"]
    assert "Check DEMO edge case 2099." in review_context
    assert "prompt_tokens" in review_context
    assert "total_tokens" in review_context
    assert "password=bad" not in review_context
    artifact = db.build_session_artifact(database_path, review["review_session_id"])
    assert artifact["token_log"][0]["usage_kind"] == "reporting"
    assert artifact["token_log"][0]["total_tokens"] == 49

def test_review_action_accepts_completed_worker_run_evidence_when_session_is_not_completed(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        session = db.create_session(
            database_path,
            task_description="Worker run evidence work",
            model="gpt-5.1-codex",
            session_key_hash="w" * 64,
            guardrail_overrides={},
            status="failed",
        )
        task = db.create_task(
            database_path,
            description="Worker run evidence work",
            status="Review",
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
            session_id=session["id"],
        )
        run = db.create_worker_run(
            database_path,
            task_id=task["id"],
            session_id=session["id"],
            adapter_id="codex",
            model="gpt-5.1-codex",
            tracking_mode="native_usage",
            command_plan={"argv": ["codex"]},
        )
        db.mark_worker_run_completed(database_path, run["id"], returncode=0, stdout="DEMO done 2099")

        response = client.post(
            f"/tasks/{task['id']}/review",
            headers=_auth_headers(),
            json={"action": "mark_done"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "Done"
    assert response.json()["session_id"] == session["id"]

def test_review_action_rejects_non_review_task_without_changing_status(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    database_path = tmp_path / "harness.db"
    with _client(tmp_path) as client:
        task = db.create_task(
            database_path,
            description="Estimated task is not reviewable",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
        )
        response = client.post(
            f"/tasks/{task['id']}/review",
            headers=_auth_headers(),
            json={"action": "mark_done"},
        )
        after = db.get_task(database_path, task["id"])

    assert response.status_code == 409
    assert "only available for tasks in Review" in response.text
    assert after["status"] == "Estimated"

def test_review_action_agent_review_failure_is_stored_and_task_remains_review(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeEstimatorLLM(exc=RuntimeError("DEMO control-plane outage 2099"))
    database_path = tmp_path / "harness.db"
    with _client_with_llm(tmp_path, llm) as client:
        session = db.create_session(
            database_path,
            task_description="Review failure work",
            model="gpt-5.1-codex",
            session_key_hash="v" * 64,
            guardrail_overrides={},
            status="completed",
        )
        task = db.create_task(
            database_path,
            description="Review failure work",
            status="Review",
            estimate_tokens=8000,
            recommended_model="gpt-5.1-codex",
            session_id=session["id"],
            metadata=project_task_metadata(db.list_connected_projects(database_path)[0]),
        )

        response = client.post(
            f"/tasks/{task['id']}/review",
            headers=_auth_headers(),
            json={"action": "agent_review"},
        )
        board = client.get("/board", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Review"
    review = body["metadata"]["agent_review"]
    assert review["status"] == "failed"
    assert review["error_type"] == "RuntimeError"
    assert "DEMO control-plane outage 2099" in review["error"]
    assert db.get_session(database_path, review["review_session_id"])["status"] == "failed"
    assert "Agent Review failed" in board.text

