from __future__ import annotations

from agile_ai_htb import db
from agile_ai_htb.demo_seed import DEMO_TASKS, seed_demo_tasks
from agile_ai_htb.launch_guardrails import evaluate_launch_guardrails


def test_seed_demo_tasks_inserts_six_estimated_tasks_once(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)

    first = seed_demo_tasks(db_path)
    second = seed_demo_tasks(db_path)
    tasks = db.list_tasks(db_path)

    assert len(first) == 6
    assert second == []
    assert len(tasks) == 6
    assert [task["id"] for task in tasks] == ["DEMO_TASK_2099_T1", "DEMO_TASK_2099_T2", "DEMO_TASK_2099_T3", "DEMO_TASK_2099_T4", "DEMO_TASK_2099_T5", "DEMO_TASK_2099_T6"]
    assert {task["status"] for task in tasks} == {"Estimated"}


def test_seeded_tasks_match_demo_plan_metadata(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)

    seed_demo_tasks(db_path)
    tasks = {task["id"]: task for task in db.list_tasks(db_path)}

    assert tasks["DEMO_TASK_2099_T1"]["estimate_tokens"] == 8_000
    assert tasks["DEMO_TASK_2099_T1"]["recommended_model"] == "Claude Haiku"
    assert tasks["DEMO_TASK_2099_T1"]["metadata"]["complexity"] == "Simple"
    assert "snip save" in tasks["DEMO_TASK_2099_T1"]["description"]
    assert tasks["DEMO_TASK_2099_T5"]["estimate_tokens"] == 90_000
    assert tasks["DEMO_TASK_2099_T5"]["recommended_model"] == "Claude Opus"
    assert tasks["DEMO_TASK_2099_T5"]["metadata"]["complexity"] == "Complex"
    assert all(task["id"] in tasks for task in DEMO_TASKS)


def test_seeded_demo_worker_has_budget_authoritative_tracking_for_gpt5_demo(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)

    seed_demo_tasks(db_path)

    adapter = db.get_worker_adapter(db_path, "demo_worker")
    assert adapter["verification_status"] == "verified"
    assert adapter["verification_evidence"]["tracking_mode"] == "proxy_governed"
    assert adapter["verification_evidence"]["tracking_authoritative"] is True
    assert "gpt-5.4-mini" in adapter["supported_models"]

    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="demo_worker",
        model="gpt-5.4-mini",
        session_api_key="sk_sess_test",
        proxy_url="http://127.0.0.1:8000/v1",
    )

    assert result.passed is True
