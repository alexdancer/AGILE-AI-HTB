import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agile_ai_htb import db
from agile_ai_htb.app import create_app
from agile_ai_htb.project_context import project_task_metadata
from agile_ai_htb.routes import portal as portal_routes
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


def _configure_codex_worker(db_path: Path, tmp_path: Path, *, tracking_mode: str = "proxy_governed"):
    db.update_worker_adapter(
        db_path,
        "codex",
        workdir=str(tmp_path),
        config={"launch_template": ["codex", "--model", "{model}"]},
        supported_models=["gpt-5.4"],
        is_default=True,
    )
    db.mark_worker_adapter_verification(
        db_path,
        "codex",
        verified=True,
        evidence={"ok": True, "tracking_mode": tracking_mode, "tracking_authoritative": tracking_mode != "observed_only"},
    )


def _codex_native_stdout() -> str:
    return "\n".join(
        [
            json.dumps({"type": "thread.started", "thread_id": "thread_2099_demo_codex_launch"}),
            json.dumps({"type": "item.completed", "item": {"text": "DEMO_2099 launch done"}}),
            json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 100,
                        "cached_input_tokens": 40,
                        "output_tokens": 20,
                        "reasoning_output_tokens": 5,
                    },
                }
            ),
        ]
    )


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
                "recommended_model": "gpt-5.4",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
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

def test_codex_launch_rejects_disallowed_model_before_runner(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []
    with _client(tmp_path) as client:
        getattr(client, "app").state.task_launch_runner = runner_calls.append
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="Launch unsupported Codex model",
            status="Estimated",
            estimate_tokens=9000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(project["root_path"]),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            tmp_path / "harness.db",
            "codex",
            verified=True,
            evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
        )

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.5"},
        )
        blocked = db.get_task(tmp_path / "harness.db", task["id"])

    assert response.status_code == 409
    assert blocked["status"] == "Estimated"
    assert "Selected model is not supported" in blocked["metadata"]["launch_blocked_reason"]
    assert runner_calls == []


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
                "recommended_model": "gpt-5.4",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"launch_template": ["codex", "--model", "{model}", "--prompt", "{prompt}"]},
            supported_models=["gpt-5.4"],
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
                "recommended_model": "gpt-5.4",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
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
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=plan.metadata["session_id"],
            usage_kind="task_execution",
            model=plan.metadata["model"],
            prompt_tokens=12,
            completion_tokens=3,
            cost=0,
            raw_usage={"total_tokens": 15},
        )
        return {"returncode": 0, "stdout": "started", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post(
            "/tasks",
            json={
                "description": "Launch from board form",
                "estimate_tokens": 8000,
                "recommended_model": "gpt-5.4",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"launch_template": ["codex", "--model", "{model}"]},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers={**_auth_headers(), "accept": "text/html"},
            data={},
            follow_redirects=False,
        )
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "completed")
        refreshed = db.get_task(tmp_path / "harness.db", task["id"])

    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{task['metadata']['connected_project_id']}/board"
    assert refreshed["status"] == "Review"
    assert len(runner_calls) == 1
    assert runner_calls[0].env["OPENAI_BASE_URL"] == "http://127.0.0.1:8000/v1"
    assert "sk_sess_" not in response.text


def test_codex_native_launch_records_normalized_usage_and_exec_command(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        (Path(plan.metadata["project_root"]) / "codex_native_result_DEMO_2099.txt").write_text("done\n")
        return {"returncode": 0, "stdout": _codex_native_stdout(), "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="Implement DEMO_2099 Codex native usage accounting",
            status="Estimated",
            estimate_tokens=9000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            tmp_path / "harness.db",
            "codex",
            verified=True,
            evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
        )

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.4", "proxy_url": "http://127.0.0.1:8000/v1"},
        )
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "completed")
        refreshed = db.get_task(tmp_path / "harness.db", task["id"])
        session_artifact = db.build_session_artifact(tmp_path / "harness.db", refreshed["session_id"])
        project_root = str(project["root_path"])

    assert response.status_code == 200
    assert refreshed["status"] == "Review"
    assert refreshed["actual_tokens"] == 85
    assert len(runner_calls) == 1
    assert runner_calls[0].command[:8] == [
        "codex",
        "exec",
        "--json",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "-m",
        "gpt-5.4",
    ]
    assert runner_calls[0].command[-3:-1] == ["--cd", project_root]
    assert runner_calls[0].cwd == Path(project_root)
    assert runner_calls[0].metadata["project_root"] == project_root
    assert refreshed["metadata"]["launch_command_plan"]["command"][:8] == [
        "codex",
        "exec",
        "--json",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "-m",
        "gpt-5.4",
    ]
    assert refreshed["metadata"]["launch_command_plan"]["cwd"] == project_root
    assert refreshed["metadata"]["launch_command_plan"]["metadata"]["project_root"] == project_root
    assert "Implement DEMO_2099 Codex native usage accounting" not in str(refreshed["metadata"]["launch_command_plan"])
    assert refreshed["metadata"]["launch_command_plan"]["metadata"]["prompt_redacted"] is True
    assert runner_calls[0].env == {}
    turn = session_artifact["token_log"][0]
    assert turn["usage_kind"] == "task_execution"
    assert turn["total_tokens"] == 125
    assert turn["raw_usage"]["usage"]["cached_input_tokens"] == 40
    assert turn["raw_usage"]["usage_source"] == "native_usage"


def test_codex_native_read_only_non_git_mutation_blocks_task(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    def fake_runner(plan):
        Path(plan.metadata["project_root"], "changed.txt").write_text("mutated\n")
        return {"returncode": 0, "stdout": _codex_native_stdout(), "stderr": ""}

    with _client(tmp_path) as client:
        getattr(client, "app").state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="Read only DEMO_2099 Codex task",
            status="Estimated",
            estimate_tokens=9000,
            recommended_model="gpt-5.4",
            metadata={**project_task_metadata(project), "launch_mode": "read_only"},
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(project["root_path"]),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            tmp_path / "harness.db",
            "codex",
            verified=True,
            evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
        )

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.4"},
        )
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "failed")
        blocked = db.get_task(tmp_path / "harness.db", task["id"])

    assert response.status_code == 200
    assert blocked["status"] == "Blocked"
    assert blocked["metadata"]["launch_blocked_reason"] == "Read-only Worker session modified the connected project."
    assert "changed.txt" in blocked["metadata"]["readonly_diff_evidence"]["after"]


def test_codex_native_launch_failed_exit_does_not_record_costless_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    def fake_runner(plan):
        return {"returncode": 1, "stdout": _codex_native_stdout(), "stderr": "DEMO_2099 Codex failed"}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="Fail DEMO_2099 Codex native usage accounting",
            status="Estimated",
            estimate_tokens=9000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            tmp_path / "harness.db",
            "codex",
            verified=True,
            evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
        )

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.4", "proxy_url": "http://127.0.0.1:8000/v1"},
        )
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "failed")
        refreshed = db.get_task(tmp_path / "harness.db", task["id"])
        session_artifact = db.build_session_artifact(tmp_path / "harness.db", refreshed["session_id"])

    assert response.status_code == 200
    assert refreshed["status"] == "Estimated"
    assert refreshed["metadata"]["launch_failure_type"] == "worker_adapter_failure"
    assert session_artifact["token_log"] == []


def test_board_shows_codex_trusted_directory_failure_as_retryable_setup_diagnostic(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    def fake_runner(plan):
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": "Not inside a trusted directory and --skip-git-repo-check was not specified. api_key=abc123 Bearer abc.def",
        }

    with _client(tmp_path) as client:
        getattr(client, "app").state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="DEMO_2099 Codex trust diagnostic task",
            status="Estimated",
            estimate_tokens=9000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(project["root_path"]),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            tmp_path / "harness.db",
            "codex",
            verified=True,
            evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
        )

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers={**_auth_headers(), "accept": "text/html"},
            data={"adapter_id": "codex", "model": "gpt-5.4"},
            follow_redirects=False,
        )
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "failed")
        refreshed = db.get_task(tmp_path / "harness.db", task["id"])
        board = client.get(f"/projects/{project['id']}/board", headers=_auth_headers())

    assert response.status_code == 303
    assert refreshed["status"] == "Estimated"
    assert refreshed["metadata"]["launch_retryable"] is True
    assert refreshed["metadata"]["launch_diagnostic"]["code"] == "codex_untrusted_directory"
    assert "Not inside a trusted directory and --skip-git-repo-check was not specified." in board.text
    assert "Open Worker Setup" in board.text
    assert "Adapter: codex" in board.text
    assert "Model: gpt-5.4" in board.text
    assert str(project["root_path"]) in board.text
    assert f'action="/tasks/{task["id"]}/launch"' in board.text
    assert "api_key=abc123" not in board.text
    assert "Bearer abc.def" not in board.text


def test_codex_native_sandbox_rejection_with_zero_exit_stays_retryable(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    def fake_runner(plan):
        return {
            "returncode": 0,
            "stdout": _codex_native_stdout(),
            "stderr": 'Rejected CreateProcess: /bin/zsh -lc "rm -rf .venv && python3 -m venv .venv && pip install -e \'[test]\'" was blocked by sandbox policy.',
        }

    with _client(tmp_path) as client:
        getattr(client, "app").state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="DEMO_2099 Codex sandbox rejected venv setup",
            status="Estimated",
            estimate_tokens=9000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(project["root_path"]),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            tmp_path / "harness.db",
            "codex",
            verified=True,
            evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
        )

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.4", "proxy_url": "http://127.0.0.1:8000/v1"},
        )
        run = _wait_for_worker_run(tmp_path / "harness.db", task["id"], "failed")
        refreshed = db.get_task(tmp_path / "harness.db", task["id"])

    assert response.status_code == 200
    assert refreshed["status"] == "Estimated"
    assert refreshed["metadata"]["launch_retryable"] is True
    assert refreshed["metadata"]["launch_failure_type"] == "worker_action_rejected"
    assert "operator approval" in refreshed["metadata"]["launch_error"]
    assert "Rejected CreateProcess" in refreshed["metadata"]["action_rejections"][0]
    assert run["error_type"] == "worker_action_rejected"


def test_board_form_recoverable_launch_error_stays_on_task_card_with_launch_form(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    def fake_runner(plan):
        return {"returncode": 124, "stdout": "", "stderr": "Command timed out after 60 seconds."}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post(
            "/tasks",
            json={
                "description": "Retryable DEMO launch timeout 2099",
                "status": "Ready",
                "estimate_tokens": 8000,
                "recommended_model": "gpt-5.4",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"launch_template": ["codex", "--model", "{model}"]},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers={**_auth_headers(), "accept": "text/html"},
            data={},
            follow_redirects=False,
        )
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "failed")
        refreshed = db.get_task(tmp_path / "harness.db", task["id"])
        board = client.get("/board", headers=_auth_headers())

    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{task['metadata']['connected_project_id']}/board"
    assert refreshed["status"] == "Estimated"
    assert refreshed["metadata"]["launch_retryable"] is True
    assert "Launch error:" in board.text
    assert "Worker adapter launch failed." in board.text
    assert "Command timed out after 60 seconds." in board.text
    assert f'action="/tasks/{task["id"]}/launch"' in board.text
    assert "Only Estimated tasks can launch." not in board.text


def test_project_board_live_refresh_controls_and_status_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    with _client(tmp_path) as client:
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="Running task",
            status="Running",
            metadata=project_task_metadata(project),
        )

        board = client.get(f"/projects/{project['id']}/board", headers=_auth_headers())
        global_board = client.get("/board", headers=_auth_headers(), follow_redirects=False)
        status_response = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers())

    assert task["status"] == "Running"
    assert board.status_code == 200
    assert "Run automation" in board.text
    assert "Eligible Estimated:" in board.text
    assert "Auto Agent Review" in board.text
    assert "Live refresh active" in board.text
    assert f"/projects/{project['id']}/board/status" in board.text
    assert global_board.status_code == 303
    assert "Run automation" not in global_board.text
    assert "Run queue" not in global_board.text
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["project_id"] == project["id"]
    assert body["counts"]["Running"] == 1
    assert body["has_active_runs"] is True
    assert body["queue_active"] is False


def test_project_board_status_endpoint_reports_terminal_worker_run_without_manual_refresh(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    def fake_runner(plan):
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=plan.metadata["session_id"],
            usage_kind="task_execution",
            model=plan.metadata["model"],
            prompt_tokens=12,
            completion_tokens=3,
            cost=0,
            raw_usage={"total_tokens": 15},
        )
        return {"returncode": 0, "stdout": "ok", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post(
            "/tasks",
            json={
                "description": "Launch for live refresh",
                "estimate_tokens": 8000,
                "recommended_model": "gpt-5.4",
            },
        ).json()
        project_id = task["metadata"]["connected_project_id"]
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"launch_template": ["codex", "--model", "{model}"]},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        launch = client.post(
            f"/tasks/{task['id']}/launch",
            headers={**_auth_headers(), "accept": "text/html"},
            data={},
            follow_redirects=False,
        )
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "completed")
        status_response = client.get(f"/projects/{project_id}/board/status", headers=_auth_headers())

    assert launch.status_code == 303
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["counts"]["Running"] == 0
    assert body["counts"]["Review"] == 1
    assert body["has_active_runs"] is False


def test_project_run_next_launches_one_project_task_with_automation_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=plan.metadata["session_id"],
            usage_kind="task_execution",
            model=plan.metadata["model"],
            prompt_tokens=12,
            completion_tokens=3,
            cost=0,
            raw_usage={"total_tokens": 15},
        )
        return {"returncode": 0, "stdout": "ok", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        first = db.create_task(
            tmp_path / "harness.db",
            description="first automated task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        second = db.create_task(
            tmp_path / "harness.db",
            description="second automated task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"launch_template": ["codex", "--model", "{model}"]},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        response = client.post(
            f"/projects/{project['id']}/run-next",
            headers=_auth_headers(),
            follow_redirects=False,
        )
        _wait_for_worker_run(tmp_path / "harness.db", first["id"], "completed")

    assert response.status_code == 303
    assert response.headers["location"] == f"/projects/{project['id']}/board"
    assert len(runner_calls) == 1
    assert db.get_task(tmp_path / "harness.db", first["id"])["metadata"]["automation_source"] == "run_next"
    assert db.get_task(tmp_path / "harness.db", second["id"])["status"] == "Estimated"


def test_project_run_queue_launches_next_after_review_without_cross_project_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=plan.metadata["session_id"],
            usage_kind="task_execution",
            model=plan.metadata["model"],
            prompt_tokens=12,
            completion_tokens=3,
            cost=0,
            raw_usage={"total_tokens": 15},
        )
        return {"returncode": 0, "stdout": "ok", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        other_root = tmp_path / "other-project"
        other_root.mkdir()
        other_project = db.upsert_connected_project(
            tmp_path / "harness.db",
            name="other-project",
            root_path=str(other_root.resolve()),
            profile={"name": "other-project", "root_path": str(other_root.resolve()), "test_command": "pytest"},
            capability={"state": "launch_ready", "can_launch": True},
        )
        first = db.create_task(
            tmp_path / "harness.db",
            description="first queue task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        second = db.create_task(
            tmp_path / "harness.db",
            description="second queue task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        other = db.create_task(
            tmp_path / "harness.db",
            description="other project task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(other_project),
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"launch_template": ["codex", "--model", "{model}"]},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        start = client.post(
            f"/projects/{project['id']}/queue/start",
            headers=_auth_headers(),
            follow_redirects=False,
        )
        _wait_for_worker_run(tmp_path / "harness.db", first["id"], "completed")
        status_response = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers())
        _wait_for_worker_run(tmp_path / "harness.db", second["id"], "completed")
        final_status = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers())

    assert start.status_code == 303
    assert status_response.status_code == 200
    assert len(runner_calls) == 2
    assert db.get_task(tmp_path / "harness.db", first["id"])["status"] == "Review"
    assert db.get_task(tmp_path / "harness.db", second["id"])["status"] == "Review"
    assert db.get_task(tmp_path / "harness.db", other["id"])["status"] == "Estimated"
    assert final_status.json()["queue"]["latest_stop_reason"] == "completed_no_eligible_tasks"


def test_project_run_queue_stops_before_budget_override(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="over budget queue task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        _configure_codex_worker(tmp_path / "harness.db", tmp_path)
        db.set_token_budget_settings(tmp_path / "harness.db", daily_cap_tokens=10, session_cap_tokens=10)

        start = client.post(f"/projects/{project['id']}/queue/start", headers=_auth_headers(), follow_redirects=False)
        body = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers()).json()

    assert start.status_code == 303
    assert db.get_task(tmp_path / "harness.db", task["id"])["status"] == "Estimated"
    assert body["queue"]["latest_stop_reason"] == "budget_approval_required"


def test_project_run_queue_stops_before_native_usage_acknowledgement(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="native usage budget queue task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        _configure_codex_worker(tmp_path / "harness.db", tmp_path, tracking_mode="native_usage")
        db.set_token_budget_settings(tmp_path / "harness.db", daily_cap_tokens=10, session_cap_tokens=10)

        start = client.post(f"/projects/{project['id']}/queue/start", headers=_auth_headers(), follow_redirects=False)
        body = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers()).json()

    assert start.status_code == 303
    refreshed = db.get_task(tmp_path / "harness.db", task["id"])
    assert refreshed["status"] == "Estimated"
    assert refreshed["metadata"]["native_usage_override_ack_required"] is True
    assert body["queue"]["latest_stop_reason"] == "native_usage_ack_required"


def test_project_run_queue_stops_on_observed_only_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        db.create_task(
            tmp_path / "harness.db",
            description="observed only queue task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        _configure_codex_worker(tmp_path / "harness.db", tmp_path, tracking_mode="observed_only")

        start = client.post(f"/projects/{project['id']}/queue/start", headers=_auth_headers(), follow_redirects=False)
        body = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers()).json()

    assert start.status_code == 303
    assert body["queue"]["status"] == "stopped"
    assert body["queue"]["latest_stop_reason"] == "launch_guardrail_blocked"


def test_project_run_queue_stops_on_retryable_worker_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    def failing_runner(plan):
        return {"returncode": 124, "stdout": "", "stderr": "timeout"}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = failing_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="retryable queue task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        _configure_codex_worker(tmp_path / "harness.db", tmp_path)

        start = client.post(f"/projects/{project['id']}/queue/start", headers=_auth_headers(), follow_redirects=False)
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "failed")
        body = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers()).json()

    assert start.status_code == 303
    refreshed = db.get_task(tmp_path / "harness.db", task["id"])
    assert refreshed["status"] == "Estimated"
    assert refreshed["metadata"]["launch_retryable"] is True
    assert body["queue"]["latest_stop_reason"] == "retryable_failure"


def test_project_run_queue_does_not_relaunch_retryable_task_without_active_pointer(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def runner(plan):
        runner_calls.append(plan)
        return {"returncode": 0, "stdout": "", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        db.create_task(
            tmp_path / "harness.db",
            description="paused retryable queue task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata={**project_task_metadata(project), "launch_retryable": True, "active_worker_run_id": "wr_DEMO_999"},
        )
        _configure_codex_worker(tmp_path / "harness.db", tmp_path)
        portal_routes.start_run_automation(
            tmp_path / "harness.db",
            project_id=project["id"],
            source=portal_routes.RUN_QUEUE_SOURCE,
            active_task_id=None,
            active_worker_run_id=None,
        )

        body = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers()).json()

    assert body["queue"]["status"] == "stopped"
    assert body["queue"]["latest_stop_reason"] == "retryable_failure"
    assert runner_calls == []


def test_project_run_queue_no_eligible_and_operator_stop_reasons(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        start = client.post(f"/projects/{project['id']}/queue/start", headers=_auth_headers(), follow_redirects=False)
        no_eligible = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers()).json()
        stop = client.post(f"/projects/{project['id']}/queue/stop", headers=_auth_headers(), follow_redirects=False)
        stopped = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers()).json()
        board = client.get(f"/projects/{project['id']}/board", headers=_auth_headers())

    assert start.status_code == 303
    assert no_eligible["queue"]["latest_stop_reason"] == "completed_no_eligible_tasks"
    assert stop.status_code == 303
    assert stopped["queue"]["latest_stop_reason"] == "operator_stop"
    assert "operator_stop" in board.text
    assert "Queue: stopped" in board.text


def test_launch_accepts_manual_estimate_payload_before_guardrails(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=plan.metadata["session_id"],
            usage_kind="task_execution",
            model=plan.metadata["model"],
            prompt_tokens=12,
            completion_tokens=3,
            cost=0,
            raw_usage={"total_tokens": 15},
        )
        return {"returncode": 0, "stdout": "started", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post("/tasks", json={"description": "Unestimated launch"}).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.4", "estimate_tokens": 9000},
        )
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "completed")

    body = response.json()
    assert response.status_code == 200
    assert body["task"]["status"] == "Running"
    assert body["task"]["estimate_tokens"] == 9000
    assert body["task"]["recommended_model"] == "gpt-5.4"
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
            recommended_model="gpt-5.4",
        )
        before_sessions = len(db.list_sessions(tmp_path / "harness.db"))

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.4", "estimate_tokens": 9000},
        )
        after = db.get_task(tmp_path / "harness.db", task["id"])

    assert response.status_code == 409
    assert after["status"] == "Done"
    assert after["estimate_tokens"] == 8000
    assert after["recommended_model"] == "gpt-5.4"
    assert len(db.list_sessions(tmp_path / "harness.db")) == before_sessions
    assert runner_calls == []

def test_launch_second_call_after_running_claim_is_rejected_without_second_runner(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        time.sleep(0.1)
        return {"returncode": 0, "stdout": "started", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post(
            "/tasks",
            json={
                "description": "Launch once only",
                "estimate_tokens": 8000,
                "recommended_model": "gpt-5.4",
            },
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
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
    assert second.status_code == 200
    assert len(db.list_worker_runs(tmp_path / "harness.db", task_id=task["id"])) == 1
    assert second.json()["launch_guardrails"].get("duplicate_active_run") is True

def test_duplicate_launch_rejects_mismatched_project_before_active_run_reuse(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        time.sleep(0.1)
        return {"returncode": 0, "stdout": "started", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        task = client.post(
            "/tasks",
            json={
                "description": "Launch only from bound board",
                "estimate_tokens": 8000,
                "recommended_model": "gpt-5.4",
            },
        ).json()
        project_a = db.get_connected_project(tmp_path / "harness.db", task["metadata"]["connected_project_id"])
        project_b_root = tmp_path / "other-project"
        project_b_root.mkdir()
        project_b = db.upsert_connected_project(
            tmp_path / "harness.db",
            name="Other Project",
            root_path=str(project_b_root.resolve()),
            profile={"name": "Other Project", "root_path": str(project_b_root.resolve()), "test_command": "pytest"},
            capability={"state": "launch_ready", "can_launch": True},
        )
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})

        first = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "proxy_url": "http://127.0.0.1:8000/v1", "project_id": project_a["id"]},
        )
        second = client.post(
            f"/tasks/{task['id']}/launch",
            headers={**_auth_headers(), "accept": "text/html"},
            data={"adapter_id": "codex", "proxy_url": "http://127.0.0.1:8000/v1", "project_id": project_b["id"]},
            follow_redirects=False,
        )

    assert first.status_code == 200
    assert second.status_code == 303
    assert second.headers["location"].startswith(f"/projects/{project_a['id']}/board?error=")
    assert len(runner_calls) == 1

@pytest.mark.parametrize("estimate_tokens", [True, 0, -1])
def test_launch_rejects_invalid_manual_estimate_tokens(tmp_path, monkeypatch, estimate_tokens):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        task = client.post("/tasks", json={"description": "Bad launch estimate"}).json()
        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"model": "gpt-5.4", "estimate_tokens": estimate_tokens},
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
                model="gpt-5.4",
                session_key_hash="d" * 64,
                guardrail_overrides={},
                status="running",
            )["id"]
        task = db.create_task(
            tmp_path / "harness.db",
            description=f"{status} task",
            status=status,
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            session_id=session_id,
        )
        before_sessions = len(db.list_sessions(tmp_path / "harness.db"))
        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "model": "gpt-5.4"},
        )
        after = db.get_task(tmp_path / "harness.db", task["id"])

    assert response.status_code == 409
    assert after["status"] == status
    assert len(db.list_sessions(tmp_path / "harness.db")) == before_sessions
    assert runner_calls == []
    assert "Only Estimated tasks can launch." in after["metadata"].get("launch_blocked_reason", "")

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
            json={"description": "Record worker tokens", "estimate_tokens": 8000, "recommended_model": "gpt-5.4"},
        ).json()
        db.update_worker_adapter(
            tmp_path / "harness.db",
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(tmp_path / "harness.db", "codex", verified=True, evidence={"ok": True})
        launched = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"adapter_id": "codex", "proxy_url": "http://127.0.0.1:8000/v1"},
        ).json()["task"]
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "completed")
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




def test_project_run_queue_auto_agent_review_stores_advisory_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeSequentialLLM(
        [
            {
                "summary": "DEMO auto review approves the work 2099.",
                "findings": [],
                "recommendation": "approve",
            }
        ]
    )

    def fake_runner(plan):
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=plan.metadata["session_id"],
            usage_kind="task_execution",
            model=plan.metadata["model"],
            prompt_tokens=12,
            completion_tokens=3,
            cost=0,
            raw_usage={"total_tokens": 15},
        )
        return {"returncode": 0, "stdout": "ok", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.llm_client = llm
        client.app.state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="auto review queue task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        _configure_codex_worker(tmp_path / "harness.db", tmp_path)

        start = client.post(
            f"/projects/{project['id']}/queue/start",
            headers=_auth_headers(),
            data={"auto_agent_review": "on"},
            follow_redirects=False,
        )
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "completed")
        status = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers())

    assert start.status_code == 303
    assert status.status_code == 200
    refreshed = db.get_task(tmp_path / "harness.db", task["id"])
    assert refreshed["status"] == "Review"
    review = refreshed["metadata"]["agent_review"]
    assert review["status"] == "completed"
    assert review["recommendation"] == "approve"
    assert len(llm.requests) == 1
    assert "auto_agent_review" in [event["kind"] for event in refreshed["metadata"]["automation_events"]]


def test_project_run_queue_auto_agent_review_failure_leaves_review(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)

    class FailingLLM:
        async def acompletion(self, request):
            raise RuntimeError("DEMO auto review outage 2099")

    def fake_runner(plan):
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=plan.metadata["session_id"],
            usage_kind="task_execution",
            model=plan.metadata["model"],
            prompt_tokens=12,
            completion_tokens=3,
            cost=0,
            raw_usage={"total_tokens": 15},
        )
        return {"returncode": 0, "stdout": "ok", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.llm_client = FailingLLM()
        client.app.state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="failing auto review queue task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        _configure_codex_worker(tmp_path / "harness.db", tmp_path)

        start = client.post(
            f"/projects/{project['id']}/queue/start",
            headers=_auth_headers(),
            data={"auto_agent_review": "on"},
            follow_redirects=False,
        )
        _wait_for_worker_run(tmp_path / "harness.db", task["id"], "completed")
        status = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers())

    assert start.status_code == 303
    assert status.status_code == 200
    refreshed = db.get_task(tmp_path / "harness.db", task["id"])
    assert refreshed["status"] == "Review"
    review = refreshed["metadata"]["agent_review"]
    assert review["status"] == "failed"
    assert "DEMO auto review outage 2099" in review["error"]


def test_project_run_queue_waits_when_manual_project_run_is_active(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        return {"returncode": 0, "stdout": "still running", "stderr": ""}

    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        running = db.create_task(
            tmp_path / "harness.db",
            description="manual running project task",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        queued = db.create_task(
            tmp_path / "harness.db",
            description="queued task must wait",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        _configure_codex_worker(tmp_path / "harness.db", tmp_path)

        db.update_task(tmp_path / "harness.db", running["id"], {"status": "Running"})
        start = client.post(f"/projects/{project['id']}/queue/start", headers=_auth_headers(), follow_redirects=False)
        status = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers()).json()

    assert start.status_code == 303
    assert len(runner_calls) == 0
    assert db.get_task(tmp_path / "harness.db", running["id"])["status"] == "Running"
    assert db.get_task(tmp_path / "harness.db", queued["id"])["status"] == "Estimated"
    assert status["queue"]["status"] == "running"
    assert status["queue"]["active_task_id"] is None


def test_auto_agent_review_claim_is_single_use(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    task = db.create_task(
        db_path,
        description="review claim task",
        status="Review",
        estimate_tokens=8000,
        recommended_model="gpt-5.4",
        metadata={},
    )

    first = db.claim_task_agent_review(db_path, task["id"], {"status": "running"})
    second = db.claim_task_agent_review(db_path, task["id"], {"status": "running"})

    assert first is not None
    assert first["metadata"]["agent_review"]["status"] == "running"
    assert second is None


def test_project_run_queue_honors_stop_after_auto_review_before_next_launch(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    runner_calls = []

    def fake_runner(plan):
        runner_calls.append(plan)
        db.record_token_turn(
            tmp_path / "harness.db",
            session_id=plan.metadata["session_id"],
            usage_kind="task_execution",
            model=plan.metadata["model"],
            prompt_tokens=12,
            completion_tokens=3,
            cost=0,
            raw_usage={"total_tokens": 15},
        )
        return {"returncode": 0, "stdout": "ok", "stderr": ""}

    async def stop_during_auto_review(request, project_id, task):
        portal_routes.stop_run_automation(
            tmp_path / "harness.db",
            project_id=project_id,
            reason="operator_stop",
            task_id=task["id"],
        )
        return task

    monkeypatch.setattr(portal_routes, "_maybe_run_auto_agent_review", stop_during_auto_review)
    with _client(tmp_path) as client:
        client.app.state.task_launch_runner = fake_runner
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        first = db.create_task(
            tmp_path / "harness.db",
            description="first queue task before stop",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        second = db.create_task(
            tmp_path / "harness.db",
            description="second queue task must not launch after stop",
            status="Estimated",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        _configure_codex_worker(tmp_path / "harness.db", tmp_path)

        start = client.post(f"/projects/{project['id']}/queue/start", headers=_auth_headers(), follow_redirects=False)
        _wait_for_worker_run(tmp_path / "harness.db", first["id"], "completed")
        status = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers()).json()

    assert start.status_code == 303
    assert len(runner_calls) == 1
    assert db.get_task(tmp_path / "harness.db", first["id"])["status"] == "Review"
    assert db.get_task(tmp_path / "harness.db", second["id"])["status"] == "Estimated"
    assert status["queue"]["status"] == "stopped"
    assert status["queue"]["latest_stop_reason"] == "operator_stop"


def test_project_run_queue_auto_agent_review_skips_without_completed_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    llm = FakeSequentialLLM([{"summary": "should not run", "recommendation": "approve", "findings": []}])
    with _client_with_llm(tmp_path, llm) as client:
        project = db.list_connected_projects(tmp_path / "harness.db")[0]
        task = db.create_task(
            tmp_path / "harness.db",
            description="review task without completed evidence",
            status="Review",
            estimate_tokens=8000,
            recommended_model="gpt-5.4",
            metadata=project_task_metadata(project),
        )
        portal_routes.start_run_automation(
            tmp_path / "harness.db",
            project_id=project["id"],
            source=portal_routes.RUN_QUEUE_SOURCE,
            auto_agent_review=True,
            active_task_id=task["id"],
            active_worker_run_id=None,
        )

        status = client.get(f"/projects/{project['id']}/board/status", headers=_auth_headers())

    refreshed = db.get_task(tmp_path / "harness.db", task["id"])
    event_kinds = [event["kind"] for event in refreshed["metadata"].get("automation_events", [])]
    assert status.status_code == 200
    assert "auto_agent_review_skipped" in event_kinds
    assert "agent_review" not in refreshed["metadata"]
    assert llm.requests == []
