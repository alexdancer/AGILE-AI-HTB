import pytest

from foreman_ai_hq import db
from foreman_ai_hq.demo_seed import seed_demo_sandbox, seed_demo_tasks
from foreman_ai_hq.routes.react_shell import _needs_you_state


def test_demo_sandbox_seeds_pipeline_floor_and_needs_you_scenario(tmp_path):
    database_path = tmp_path / "DEMO_2099_999.db"
    result = seed_demo_sandbox(database_path, tmp_path / "DEMO_REPO_2099_999")
    project = result["project"]
    tasks = {task["id"]: task for task in db.list_tasks(database_path)}

    assert {task["status"] for task in tasks.values()} == {
        "Estimated", "Running", "Review", "Done",
    }
    assert tasks["DEMO_TASK_2099_T3"]["session_id"] == "DEMO_SESSION_2099_RUNNING_999"
    assert tasks["DEMO_TASK_2099_T4"]["actual_tokens"] == 31_999
    assert tasks["DEMO_TASK_2099_T4"]["metadata"]["agent_review"]["findings"][0]["path"] == "snip.py"
    assert tasks["DEMO_TASK_2099_T5"]["actual_tokens"] == 84_999
    assert tasks["DEMO_TASK_2099_T2"]["metadata"]["blocked_condition"]["origin"] == "estimation"
    assert tasks["DEMO_TASK_2099_T4"]["metadata"]["blocked_condition"]["origin"] == "review"
    assert tasks["DEMO_TASK_2099_T6"]["metadata"]["blocked_condition"]["origin"] == "launch_guardrail"

    breakdowns = db.list_task_breakdowns_for_project(database_path, project["id"])
    assert [(item["id"], item["status"]) for item in breakdowns] == [
        ("DEMO_BREAKDOWN_2099_999", "proposed"),
    ]
    assert breakdowns[0]["intake_metadata"]["demo_schema_version"] == 2
    needs_you = _needs_you_state(database_path, project["id"])
    assert [item["kind"] for item in needs_you["items"]] == [
        "breakdown_review",
        "manual_estimate",
        "review_disposition",
        "budget_override",
    ]

    artifact = db.build_session_artifact(database_path, "DEMO_SESSION_2099_REVIEW_999")
    assert [item["total_tokens"] for item in artifact["token_log"]] == [31_999]
    assert [item["zone"] for item in artifact["guardrail_snapshots"]] == ["yellow"]
    assert [item["type"] for item in artifact["alarms"]] == ["BUDGET_YELLOW"]
    assert artifact["alarms"][0]["context"]["demo_schema_version"] == 2
    assert [item["name"] for item in artifact["checkpoint_results"]] == ["demo_contract"]
    assert artifact["worker_runs"][0]["stdout"].startswith("DEMO 2099 Worker output")
    assert artifact["worker_runs"][0]["metadata"]["demo_schema_version"] == 2
    assert artifact["worker_runs"][0]["metadata"]["repo_context_brief"]["documents"] == [
        {"path": "README.md"},
    ]
    assert [item["kind"] for item in artifact["worker_run_events"]] == ["worker_output"]
    assert db.get_session(database_path, "DEMO_SESSION_2099_REVIEW_999")["task_description"].endswith(
        "schema 2"
    )

    repeated = seed_demo_sandbox(database_path, tmp_path / "DEMO_REPO_2099_999")
    assert repeated["inserted_tasks"] == []
    assert repeated["planning_breakdown"]["id"] == "DEMO_BREAKDOWN_2099_999"
    assert len(db.list_tasks(database_path)) == 6
    repeated_artifact = db.build_session_artifact(database_path, "DEMO_SESSION_2099_REVIEW_999")
    assert {key: len(repeated_artifact[key]) for key in (
        "token_log", "guardrail_snapshots", "alarms", "checkpoint_results",
        "worker_runs", "worker_run_events",
    )} == {
        "token_log": 1,
        "guardrail_snapshots": 1,
        "alarms": 1,
        "checkpoint_results": 1,
        "worker_runs": 1,
        "worker_run_events": 1,
    }


def test_demo_sandbox_upgrades_board_only_seed_with_project_binding(tmp_path):
    database_path = tmp_path / "DEMO_2099_999.db"
    assert len(seed_demo_tasks(database_path)) == 6

    result = seed_demo_sandbox(database_path, tmp_path / "DEMO_REPO_2099_999")

    assert result["inserted_tasks"] == []
    assert {
        task["metadata"].get("connected_project_id")
        for task in db.list_tasks(database_path)
    } == {result["project"]["id"]}


def test_demo_sandbox_upgrades_legacy_demo_task_state(tmp_path):
    database_path = tmp_path / "DEMO_2099_999.db"
    seed_demo_tasks(database_path)
    for task in db.list_tasks(database_path):
        metadata = dict(task["metadata"])
        metadata.pop("demo_schema_version", None)
        metadata.pop("read_only", None)
        metadata.pop("blocked_condition", None)
        db.update_task(database_path, task["id"], {
            "status": "Estimated",
            "actual_tokens": None,
            "session_id": None,
            "metadata": metadata,
        })

    result = seed_demo_sandbox(database_path, tmp_path / "DEMO_REPO_2099_999")
    tasks = {task["id"]: task for task in db.list_tasks(database_path)}

    assert tasks["DEMO_TASK_2099_T3"]["status"] == "Running"
    assert tasks["DEMO_TASK_2099_T3"]["session_id"] == "DEMO_SESSION_2099_RUNNING_999"
    assert tasks["DEMO_TASK_2099_T4"]["status"] == "Review"
    assert tasks["DEMO_TASK_2099_T4"]["actual_tokens"] == 31_999
    assert tasks["DEMO_TASK_2099_T4"]["metadata"]["blocked_condition"]["origin"] == "review"
    assert all(task["metadata"]["read_only"] is True for task in tasks.values())
    assert {task["metadata"]["connected_project_id"] for task in tasks.values()} == {
        result["project"]["id"],
    }


def test_demo_sandbox_preserves_existing_default_worker_adapter(tmp_path):
    database_path = tmp_path / "DEMO_2099_999.db"
    db.init_db(database_path)
    db.update_worker_adapter(database_path, "codex", is_default=True)

    seed_demo_sandbox(database_path, tmp_path / "DEMO_REPO_2099_999")

    defaults = [adapter["id"] for adapter in db.list_worker_adapters(database_path) if adapter["is_default"]]
    assert defaults == ["codex"]
    assert db.get_worker_adapter(database_path, "demo_worker")["is_default"] is False


def test_demo_sandbox_refuses_to_overwrite_existing_project(tmp_path):
    project_root = tmp_path / "existing-project"
    project_root.mkdir()
    readme = project_root / "README.md"
    readme.write_text("# Real project\n", encoding="utf-8")

    with pytest.raises(ValueError, match="refusing to overwrite non-demo project root"):
        seed_demo_sandbox(tmp_path / "DEMO_2099_999.db", project_root)

    assert readme.read_text(encoding="utf-8") == "# Real project\n"
    assert not (project_root / "snip.py").exists()


def test_demo_sandbox_rejects_task_id_collision_before_repo_or_adapter_changes(tmp_path):
    database_path = tmp_path / "DEMO_2099_999.db"
    project_root = tmp_path / "DEMO_REPO_2099_999"
    db.init_db(database_path)
    with db.connect(database_path) as conn:
        conn.execute(
            """insert into tasks (id, description, status, metadata_json, created_at)
               values (?, ?, ?, ?, ?)""",
            (
                "DEMO_TASK_2099_T3",
                "Non-demo operator task",
                "Estimated",
                "{}",
                "2099-01-01T00:00:00+00:00",
            ),
        )

    with pytest.raises(RuntimeError, match="refusing to replace non-demo task"):
        seed_demo_sandbox(database_path, project_root)

    assert not project_root.exists()
    assert "demo_worker" not in {adapter["id"] for adapter in db.list_worker_adapters(database_path)}
    assert [task["id"] for task in db.list_tasks(database_path)] == ["DEMO_TASK_2099_T3"]


def test_demo_sandbox_rejects_session_collision_without_attaching_evidence(tmp_path):
    database_path = tmp_path / "DEMO_2099_SESSION_COLLISION_999.db"
    project_root = tmp_path / "DEMO_REPO_2099_SESSION_COLLISION_999"
    db.init_db(database_path)
    with db.connect(database_path) as conn:
        conn.execute(
            """insert into sessions
               (id, task_description, model, session_key_hash, started_at, status, guardrail_overrides_json)
               values (?, ?, ?, ?, ?, ?, ?)""",
            (
                "DEMO_SESSION_2099_REVIEW_999",
                "Operator-owned session",
                "claude-sonnet-5",
                "operator-hash",
                "2099-01-01T00:00:00+00:00",
                "completed",
                "{}",
            ),
        )
    before = _demo_owned_row_counts(database_path)

    with pytest.raises(RuntimeError, match="refusing to replace non-demo session"):
        seed_demo_sandbox(database_path, project_root)

    assert not project_root.exists()
    assert _demo_owned_row_counts(database_path) == before
    assert db.build_session_artifact(database_path, "DEMO_SESSION_2099_REVIEW_999")["worker_runs"] == []


def test_demo_sandbox_rejects_breakdown_collision_without_creating_sandbox_state(tmp_path):
    database_path = tmp_path / "DEMO_2099_BREAKDOWN_COLLISION_999.db"
    project_root = tmp_path / "DEMO_REPO_2099_BREAKDOWN_COLLISION_999"
    db.init_db(database_path)
    breakdown = db.create_task_breakdown(
        database_path,
        source_text="# Operator intake",
        source_sha256="a" * 64,
        intake_metadata={"source_name": "operator.md"},
        status="proposed",
        decision="pending_review",
        model="operator-model",
    )
    with db.connect(database_path) as conn:
        conn.execute(
            "update task_breakdowns set id = ? where id = ?",
            ("DEMO_BREAKDOWN_2099_999", breakdown["id"]),
        )
    before = _demo_owned_row_counts(database_path)

    with pytest.raises(RuntimeError, match="refusing to replace non-demo Task Breakdown"):
        seed_demo_sandbox(database_path, project_root)

    assert not project_root.exists()
    assert _demo_owned_row_counts(database_path) == before
    assert db.get_task_breakdown(database_path, "DEMO_BREAKDOWN_2099_999")["source_text"] == "# Operator intake"


@pytest.mark.parametrize("collision", ["worker_run", "alarm"])
def test_demo_sandbox_rejects_evidence_id_collision_without_other_mutation(tmp_path, collision):
    database_path = tmp_path / f"DEMO_2099_{collision.upper()}_COLLISION_999.db"
    project_root = tmp_path / f"DEMO_REPO_2099_{collision.upper()}_COLLISION_999"
    db.init_db(database_path)
    with db.connect(database_path) as conn:
        conn.execute(
            """insert into sessions
               (id, task_description, model, session_key_hash, started_at, status, guardrail_overrides_json)
               values (?, ?, ?, ?, ?, ?, ?)""",
            (
                "operator-session",
                "Operator-owned session",
                "operator-model",
                "operator-hash",
                "2099-01-01T00:00:00+00:00",
                "completed",
                "{}",
            ),
        )
        conn.execute(
            """insert into tasks (id, description, status, session_id, metadata_json, created_at)
               values (?, ?, ?, ?, ?, ?)""",
            (
                "operator-task",
                "Operator-owned task",
                "Done",
                "operator-session",
                "{}",
                "2099-01-01T00:00:00+00:00",
            ),
        )
        if collision == "worker_run":
            conn.execute(
                """insert into worker_runs
                   (id, task_id, session_id, adapter_id, model, tracking_mode, status,
                    command_plan_json, metadata_json, created_at)
                   values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "DEMO_WORKER_RUN_2099_REVIEW_999",
                    "operator-task",
                    "operator-session",
                    "codex",
                    "operator-model",
                    "external_measurement",
                    "completed",
                    "{}",
                    "{}",
                    "2099-01-01T00:00:00+00:00",
                ),
            )
        else:
            conn.execute(
                """insert into alarms
                   (id, session_id, type, severity, context_json, recommended_action, created_at)
                   values (?, ?, ?, ?, ?, ?, ?)""",
                (
                    "DEMO_ALARM_2099_REVIEW_999",
                    "operator-session",
                    "OPERATOR_ALARM",
                    "HIGH",
                    "{}",
                    "Investigate operator alarm.",
                    "2099-01-01T00:00:00+00:00",
                ),
            )
    before = _demo_owned_row_counts(database_path)

    with pytest.raises(RuntimeError, match="refusing to replace non-demo"):
        seed_demo_sandbox(database_path, project_root)

    assert not project_root.exists()
    assert _demo_owned_row_counts(database_path) == before


def _demo_owned_row_counts(database_path):
    tables = (
        "tasks",
        "sessions",
        "worker_runs",
        "alarms",
        "task_breakdowns",
        "connected_projects",
    )
    with db.connect(database_path) as conn:
        return {table: conn.execute(f"select count(*) from {table}").fetchone()[0] for table in tables}
