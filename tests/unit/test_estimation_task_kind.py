from foreman_ai_hq import db
from foreman_ai_hq.estimation_calibration import build_calibration_selection
from foreman_ai_hq.task_kind import with_task_kind


def _create_done_task(database_path, *, estimate_tokens, actual_tokens, task_kind="implementation"):
    task = db.create_task(
        database_path,
        description="demo task",
        status="Done",
        estimate_tokens=estimate_tokens,
        actual_tokens=actual_tokens,
        metadata=with_task_kind({}, task_kind),
    )
    return task


class TestEstimationAccuracyExcludesScouts:
    def test_includes_implementation_only(self, tmp_path):
        db_path = tmp_path / "harness.db"
        db.init_db(db_path)
        _create_done_task(db_path, estimate_tokens=100, actual_tokens=120, task_kind="implementation")
        _create_done_task(db_path, estimate_tokens=100, actual_tokens=300, task_kind="scout")
        accuracy = db.estimation_accuracy(db_path)
        assert accuracy["completed_count"] == 1
        assert accuracy["median_error_ratio"] == 1.2

    def test_legacy_untyped_tasks_are_implementation(self, tmp_path):
        db_path = tmp_path / "harness.db"
        db.init_db(db_path)
        task = db.create_task(
            db_path,
            description="legacy task",
            status="Done",
            estimate_tokens=100,
            actual_tokens=110,
            metadata={},
        )
        assert task["metadata"].get("task_kind") is None
        accuracy = db.estimation_accuracy(db_path)
        assert accuracy["completed_count"] == 1
        assert accuracy["median_error_ratio"] == 1.1


class TestCalibrationSelectionTaskKind:
    def test_scout_does_not_match_implementation_cases(self, tmp_path):
        # Default catalog contains implementation cases only; Scout should find none.
        selection = build_calibration_selection(
            task_description="investigate module coupling",
            project_root=str(tmp_path),
            task_kind="scout",
            limit=3,
        )
        assert selection.cases == []
