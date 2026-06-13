from __future__ import annotations

from agile_ai_htb import db
from agile_ai_htb.demo_seed import DEMO_TASKS, seed_demo_tasks


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
