from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from foreman_ai_hq import db
from foreman_ai_hq.adapter_readiness import evaluate_adapter_readiness
from foreman_ai_hq.app import create_app
from foreman_ai_hq.launch_guardrails import evaluate_launch_guardrails
from foreman_ai_hq.project_context import project_task_metadata
from foreman_ai_hq.settings import Settings
from foreman_ai_hq.worker_adapters import get_adapter_builder


ROOT = Path(__file__).resolve().parents[2]
PORTAL_TOKEN = "test-portal-token"


def _auth_headers():
    return {"Authorization": f"Bearer {PORTAL_TOKEN}"}


def _client(tmp_path: Path):
    settings = Settings(
        database_path=tmp_path / "harness.db",
        guardrails_path=ROOT / "guardrails.yaml",
    )
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


def _codex_native_stdout() -> str:
    return "\n".join(
        [
            json.dumps({"type": "thread.started", "thread_id": "thread_scout_readonly"}),
            json.dumps({"type": "item.completed", "item": {"text": "Scout done"}}),
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


def _wait_for_worker_run(db_path: Path, task_id: str, status: str):
    import time
    deadline = time.time() + 2
    while time.time() < deadline:
        runs = db.list_worker_runs(db_path, task_id=task_id)
        if runs and runs[-1]["status"] == status:
            return runs[-1]
        time.sleep(0.01)
    raise AssertionError("worker run did not reach expected status")


class FakeCodexRunner:
    def __init__(self, *, mutate: bool = False, fail: bool = False):
        self.mutate = mutate
        self.fail = fail
        self.calls: list = []

    def __call__(self, plan):
        self.calls.append(plan)
        if self.mutate:
            Path(plan.metadata["project_root"], "changed.txt").write_text("mutated\n")
        if self.fail:
            return {"returncode": 1, "stdout": "", "stderr": "setup failed"}
        return {"returncode": 0, "stdout": _codex_native_stdout(), "stderr": ""}


def test_codex_read_only_launch_keeps_sandbox_read_only(tmp_path):
    adapter = {
        "id": "codex",
        "kind": "codex",
        "name": "Codex CLI",
        "workdir": str(tmp_path),
        "config": {"command": "codex"},
        "supported_models": ["gpt-5.6-terra"],
    }
    plan = get_adapter_builder(adapter).build_native_launch_command(
        model="gpt-5.6-terra",
        task_prompt="Investigate repo layout.",
        project_root=str(tmp_path),
        read_only=True,
    )
    sandbox_index = plan.command.index("--sandbox")
    assert plan.command[sandbox_index + 1] == "read-only"
    assert plan.metadata["read_only"] is True
    assert "--skip-git-repo-check" in plan.command


def test_codex_read_only_overrides_workspace_write_template(tmp_path):
    adapter = {
        "id": "codex",
        "kind": "codex",
        "name": "Codex CLI",
        "workdir": str(tmp_path),
        "config": {
            "native_launch_template": [
                "codex",
                "exec",
                "--json",
                "--skip-git-repo-check",
                "--sandbox",
                "workspace-write",
                "-m",
                "{model}",
                "--cd",
                "{workdir}",
                "{prompt}",
            ]
        },
        "supported_models": ["gpt-5.6-terra"],
    }
    plan = get_adapter_builder(adapter).build_native_launch_command(
        model="gpt-5.6-terra",
        task_prompt="Investigate repo layout.",
        project_root=str(tmp_path),
        read_only=True,
    )
    sandbox_index = plan.command.index("--sandbox")
    assert plan.command[sandbox_index + 1] == "read-only"


@pytest.mark.parametrize("bypass_flag", ["--full-auto", "--dangerously-bypass-approvals-and-sandbox"])
def test_codex_read_only_rejects_sandbox_bypass_flags(tmp_path, bypass_flag):
    adapter = {
        "id": "codex",
        "kind": "codex",
        "name": "Codex CLI",
        "workdir": str(tmp_path),
        "config": {
            "native_launch_template": [
                "codex", "exec", bypass_flag, "-m", "{model}", "--cd", "{workdir}", "{prompt}"
            ]
        },
        "supported_models": ["gpt-5.6-terra"],
    }

    readiness = evaluate_adapter_readiness(
        {
            **adapter,
            "verification_status": "verified",
            "verification_evidence": {
                "tracking_mode": "native_usage",
                "tracking_authoritative": True,
            },
        },
        model="gpt-5.6-terra",
    )
    assert readiness.read_only_launchable is False
    assert "bypass" in " ".join(readiness.read_only_reasons).lower()

    with pytest.raises(ValueError, match="bypass.*read-only sandbox"):
        get_adapter_builder(adapter).build_native_launch_command(
            model="gpt-5.6-terra",
            task_prompt="Investigate repo layout.",
            project_root=str(tmp_path),
            read_only=True,
        )


def test_codex_standard_launch_rewrites_explicit_read_only_sandbox(tmp_path):
    adapter = {
        "id": "codex",
        "kind": "codex",
        "name": "Codex CLI",
        "workdir": str(tmp_path),
        "config": {
            "native_launch_template": [
                "codex",
                "exec",
                "--json",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "-m",
                "{model}",
                "{prompt}",
            ]
        },
        "supported_models": ["gpt-5.6-terra"],
    }
    plan = get_adapter_builder(adapter).build_native_launch_command(
        model="gpt-5.6-terra",
        task_prompt="Implement the task.",
        project_root=str(tmp_path),
        read_only=False,
    )
    sandbox_index = plan.command.index("--sandbox")
    assert plan.command[sandbox_index + 1] == "workspace-write"


def test_evaluate_adapter_readiness_codex_read_only_and_others_not():
    codex = {
        "id": "codex",
        "kind": "codex",
        "config": {"command": "codex"},
        "supported_models": ["gpt-5.6-terra"],
        "verification_status": "verified",
        "verification_evidence": {"ok": True, "tracking_mode": "native_usage", "tracking_authoritative": True},
    }
    claude = {
        "id": "claude_code",
        "kind": "claude_code",
        "config": {"command": "claude"},
        "supported_models": ["claude-sonnet-4"],
        "verification_status": "verified",
        "verification_evidence": {"ok": True, "tracking_mode": "proxy_governed", "tracking_authoritative": True},
    }
    observed = {
        "id": "codex",
        "kind": "codex",
        "config": {"command": "codex"},
        "supported_models": ["gpt-5.6-terra"],
        "verification_status": "verified",
        "verification_evidence": {"ok": True, "tracking_mode": "observed_only"},
    }

    codex_ready = evaluate_adapter_readiness(codex, model="gpt-5.6-terra")
    assert codex_ready.read_only_launchable is True
    assert codex_ready.launchable_for_board is True

    claude_ready = evaluate_adapter_readiness(claude, model="claude-sonnet-4")
    assert claude_ready.read_only_launchable is False
    assert "verified read-only launch profile" in " ".join(claude_ready.read_only_reasons).lower()
    assert claude_ready.launchable_for_board is True

    observed_ready = evaluate_adapter_readiness(observed, model="gpt-5.6-terra")
    assert observed_ready.read_only_launchable is False
    assert observed_ready.launchable_for_board is False


def test_launch_guardrail_requires_read_only_profile_for_scout(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    codex = db.get_worker_adapter(db_path, "codex")
    db.update_worker_adapter(
        db_path,
        "codex",
        config={**codex.get("config", {}), "command": "codex"},
        supported_models=["gpt-5.6-terra"],
        is_default=True,
    )
    db.mark_worker_adapter_verification(
        db_path,
        "codex",
        verified=True,
        evidence={"ok": True, "tracking_mode": "native_usage", "tracking_authoritative": True},
    )

    # No claude_code adapter present, so the guardrail passes for codex+scout
    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="codex",
        model="gpt-5.6-terra",
        session_api_key=None,
        proxy_url=None,
        read_only=True,
        read_only_profile_required=True,
    )
    assert result.passed is True
    assert result.adapter["kind"] == "codex"


def test_launch_guardrail_blocks_scout_without_read_only_profile(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "claude_code",
        config={"command": "claude"},
        supported_models=["claude-sonnet-4"],
        is_default=True,
    )
    db.mark_worker_adapter_verification(
        db_path,
        "claude_code",
        verified=True,
        evidence={"ok": True, "tracking_mode": "proxy_governed", "tracking_authoritative": True},
    )

    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="claude_code",
        model="claude-sonnet-4",
        session_api_key="sk-test",
        proxy_url="http://127.0.0.1:8000/v1",
        read_only=True,
        read_only_profile_required=True,
    )
    assert result.passed is False
    assert any("read-only" in r.lower() for r in result.reasons)


def test_scout_launch_command_plan_is_read_only_without_task_branch(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        db_path = client.app.state.settings.database_path
        project = db.list_connected_projects(db_path)[0]
        db.update_worker_adapter(
            db_path,
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.6-terra"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            db_path,
            "codex",
            verified=True,
            evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
        )
        task = db.create_task(
            db_path,
            task_id="scout-launch",
            description="Investigate repo layout",
            status="Estimated",
            estimate_tokens=1000,
            recommended_model="gpt-5.6-terra",
            metadata={
                "task_kind": "scout",
                "confidence": 0.7,
                "estimation_source": "llm",
                "estimate_revision": 1,
                **project_task_metadata(project),
            },
        )
        runner = FakeCodexRunner()
        client.app.state.task_launch_runner = runner

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"model": "gpt-5.6-terra"},
        )
        _wait_for_worker_run(db_path, task["id"], "completed")
        refreshed = db.get_task(db_path, task["id"])
        plan = refreshed["metadata"]["launch_command_plan"]

    assert response.status_code == 200
    assert refreshed["status"] == "Review"
    assert plan["metadata"]["launch_mode"] == "read_only"
    assert plan["metadata"]["read_only"] is True
    assert "task_branch" not in plan["metadata"]
    assert "--sandbox" in plan["command"]
    assert plan["command"][plan["command"].index("--sandbox") + 1] == "read-only"
    assert runner.calls[0].metadata["project_root"] == str(project["root_path"])


def test_scout_launch_blocks_claude_code_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        db_path = client.app.state.settings.database_path
        project = db.list_connected_projects(db_path)[0]
        db.update_worker_adapter(
            db_path,
            "claude_code",
            workdir=str(tmp_path),
            config={"command": "claude"},
            supported_models=["claude-sonnet-4"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            db_path,
            "claude_code",
            verified=True,
            evidence={"tracking_mode": "proxy_governed", "tracking_authoritative": True},
        )
        task = db.create_task(
            db_path,
            task_id="scout-claude",
            description="Investigate repo layout",
            status="Estimated",
            estimate_tokens=1000,
            recommended_model="claude-sonnet-4",
            metadata={
                "task_kind": "scout",
                "confidence": 0.7,
                "estimation_source": "llm",
                "estimate_revision": 1,
                **project_task_metadata(project),
            },
        )

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers={**_auth_headers(), "accept": "application/json"},
            json={"adapter_id": "claude_code", "model": "claude-sonnet-4"},
        )
        refreshed = db.get_task(db_path, task["id"])

    assert response.status_code == 409
    body = response.json()
    assert body["ok"] is False
    assert "read-only" in body["error"].lower()
    assert refreshed["status"] == "Estimated"


def test_scout_read_only_mutation_blocks_task(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        db_path = client.app.state.settings.database_path
        project = db.list_connected_projects(db_path)[0]
        db.update_worker_adapter(
            db_path,
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.6-terra"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            db_path,
            "codex",
            verified=True,
            evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
        )
        task = db.create_task(
            db_path,
            task_id="scout-mutate",
            description="Investigate repo layout",
            status="Estimated",
            estimate_tokens=1000,
            recommended_model="gpt-5.6-terra",
            metadata={
                "task_kind": "scout",
                "confidence": 0.7,
                "estimation_source": "llm",
                "estimate_revision": 1,
                **project_task_metadata(project),
            },
        )
        client.app.state.task_launch_runner = FakeCodexRunner(mutate=True)

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers=_auth_headers(),
            json={"model": "gpt-5.6-terra"},
        )
        _wait_for_worker_run(db_path, task["id"], "failed")
        refreshed = db.get_task(db_path, task["id"])

    assert response.status_code == 200
    assert refreshed["status"] == "Review"
    assert refreshed["metadata"]["launch_blocked_reason"] == "Read-only Worker session modified the connected project."
    assert refreshed["metadata"]["blocked_condition"]["origin"] == "read_only_mutation"
    assert "changed.txt" in refreshed["metadata"]["readonly_diff_evidence"]["after"]


def test_observed_only_adapter_cannot_launch_scout(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        db_path = client.app.state.settings.database_path
        project = db.list_connected_projects(db_path)[0]
        db.update_worker_adapter(
            db_path,
            "codex",
            workdir=str(tmp_path),
            config={"command": "codex"},
            supported_models=["gpt-5.6-terra"],
            is_default=True,
        )
        db.mark_worker_adapter_verification(
            db_path,
            "codex",
            verified=True,
            evidence={"tracking_mode": "observed_only"},
        )
        task = db.create_task(
            db_path,
            task_id="scout-observed",
            description="Investigate repo layout",
            status="Estimated",
            estimate_tokens=1000,
            recommended_model="gpt-5.6-terra",
            metadata={
                "task_kind": "scout",
                "confidence": 0.7,
                "estimation_source": "llm",
                "estimate_revision": 1,
                **project_task_metadata(project),
            },
        )

        response = client.post(
            f"/tasks/{task['id']}/launch",
            headers={**_auth_headers(), "accept": "application/json"},
            json={"adapter_id": "codex", "model": "gpt-5.6-terra"},
        )

    assert response.status_code == 409
    body = response.json()
    assert body["ok"] is False
    assert "observed-only" in body["error"].lower() or "budget-authoritative" in body["error"].lower()
