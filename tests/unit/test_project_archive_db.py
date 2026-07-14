import sqlite3

from foreman_ai_hq import db


def test_connected_project_archive_columns_migrate_existing_rows(tmp_path):
    db_path = tmp_path / "harness.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            create table connected_projects (
                id text primary key,
                name text not null,
                root_path text not null unique,
                profile_json text not null default '{}',
                capability_json text not null default '{}',
                backend_id text not null default 'local_runner',
                created_at text not null,
                updated_at text not null
            );
            insert into connected_projects (
                id, name, root_path, profile_json, capability_json, backend_id, created_at, updated_at
            ) values (
                'proj_999', 'Existing', '/tmp/existing-project-999', '{}', '{}', 'local_runner',
                '2099-01-01T00:00:00+00:00', '2099-01-01T00:00:00+00:00'
            );
            """
        )

    db.init_db(db_path)

    with db.connect(db_path) as conn:
        columns = {row["name"] for row in conn.execute("pragma table_info(connected_projects)").fetchall()}
    project = db.get_connected_project(db_path, "proj_999")
    assert {"archived_at", "archived_by"}.issubset(columns)
    assert project["archived_at"] is None
    assert project["archived_by"] is None
    assert db.list_connected_projects(db_path)[0]["id"] == "proj_999"


def test_connected_project_archive_restore_and_reopen_preserves_history(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    root = tmp_path / "repo"
    root.mkdir()
    project = db.upsert_connected_project(
        db_path,
        name="repo",
        root_path=str(root),
        profile={"test_command": "pytest"},
        capability={"state": "launch_ready"},
    )
    task = db.create_task(
        db_path,
        description="Preserve task history",
        status="Done",
        metadata={"connected_project_id": project["id"]},
    )

    archived = db.archive_connected_project(db_path, project["id"], archived_by="test")
    archived_again = db.archive_connected_project(db_path, project["id"], archived_by="other")

    assert db.project_is_archived(archived)
    assert archived_again["archived_at"] == archived["archived_at"]
    assert archived_again["archived_by"] == "test"
    assert db.list_connected_projects(db_path) == []
    assert [item["id"] for item in db.list_archived_connected_projects(db_path)] == [project["id"]]
    assert db.get_task(db_path, task["id"])["description"] == "Preserve task history"

    restored = db.restore_connected_project(db_path, project["id"])
    assert restored["archived_at"] is None
    assert [item["id"] for item in db.list_connected_projects(db_path)] == [project["id"]]

    db.archive_connected_project(db_path, project["id"])
    reopened = db.upsert_connected_project(
        db_path,
        name="repo",
        root_path=str(root),
        profile={"test_command": "pytest -q"},
        capability={"state": "analysis_ready"},
    )
    assert reopened["id"] == project["id"]
    assert reopened["archived_at"] is None
    assert db.get_task(db_path, task["id"])["metadata"]["connected_project_id"] == project["id"]
