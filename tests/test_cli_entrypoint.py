from pathlib import Path

from agile_ai_htb import db
from agile_ai_htb.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_bare_htb_defaults_to_serve(monkeypatch, tmp_path):
    calls = []

    def fake_run(app_ref, **kwargs):
        calls.append((app_ref, kwargs))

    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", fake_run)

    exit_code = main([
        "--database-path",
        str(tmp_path / "harness.db"),
        "--guardrails-path",
        str(ROOT / "guardrails.yaml"),
    ])

    assert exit_code == 0
    assert calls == [
        (
            "agile_ai_htb.app:create_app",
            {
                "host": "127.0.0.1",
                "port": 8000,
                "proxy_headers": False,
                "factory": True,
                "env_file": None,
            },
        )
    ]


def test_serve_cli_arguments_override_environment(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setenv("TOKEN_TRACKER_DATABASE_PATH", "env-harness.db")
    monkeypatch.setenv("TOKEN_TRACKER_GUARDRAILS_PATH", "env-guardrails.yaml")
    monkeypatch.setattr("agile_ai_htb.cli.uvicorn.run", lambda app_ref, **kwargs: calls.append((app_ref, kwargs)))

    exit_code = main([
        "serve",
        "--host",
        "0.0.0.0",
        "--port",
        "9009",
        "--database-path",
        str(tmp_path / "cli-harness.db"),
        "--guardrails-path",
        str(ROOT / "guardrails.yaml"),
    ])

    assert exit_code == 0
    assert calls[0][1]["host"] == "0.0.0.0"
    assert calls[0][1]["port"] == 9009
    assert calls[0][1]["factory"] is True
    assert calls[0][1]["env_file"] is None


def test_seed_demo_inserts_synthetic_tasks(tmp_path, capsys):
    db_path = tmp_path / "harness.db"

    exit_code = main(["--database-path", str(db_path), "seed-demo"])

    assert exit_code == 0
    tasks = {task["id"]: task for task in db.list_tasks(db_path)}
    assert "DEMO_TASK_2099_T1" in tasks
    assert "DEMO_TASK_2099_T6" in tasks
    assert "inserted 6" in capsys.readouterr().out


def test_seed_demo_is_idempotent(tmp_path, capsys):
    db_path = tmp_path / "harness.db"

    assert main(["--database-path", str(db_path), "seed-demo"]) == 0
    assert main(["--database-path", str(db_path), "seed-demo"]) == 0

    assert len(db.list_tasks(db_path)) == 6
    assert "inserted 0" in capsys.readouterr().out
