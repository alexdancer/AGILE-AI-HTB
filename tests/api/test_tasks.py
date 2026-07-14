import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from foreman_ai_hq import db
from foreman_ai_hq.app import create_app
from foreman_ai_hq.project_context import project_task_metadata
from foreman_ai_hq.settings import Settings
from foreman_ai_hq.task_launch import refresh_task_from_session


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
            "confidence": 0.82,
            "rationale": "Endpoint plus tests is a modest task.",
            "assumptions": ["No schema migration is needed."],
            "risk_flags": ["integration tests may expand scope"],
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
    assert updated.json()["status"] == "Estimated"
    assert updated.json()["estimate_tokens"] == 12_000
    assert updated.json()["recommended_model"] == "claude-haiku"
    assert updated.json()["description"] == "Add save command and tests"

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
    metadata = updated.json()["metadata"]
    assert metadata["blocked_reason"] == "Unsupported task status: Backlog"
    assert metadata["original_status"] == "Backlog"

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

def test_update_missing_task_returns_404(tmp_path):
    with _client(tmp_path) as client:
        response = client.put("/tasks/missing", json={"status": "Done"})

    assert response.status_code == 404

