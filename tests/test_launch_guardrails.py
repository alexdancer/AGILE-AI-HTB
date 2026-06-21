from agile_ai_htb import db
from agile_ai_htb.launch_guardrails import evaluate_launch_guardrails


def test_launch_guardrails_pass_when_adapter_and_proxy_ready(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "codex",
        workdir=str(tmp_path),
        config={"command": "codex"},
        supported_models=["gpt-5.1-codex"],
    )
    db.mark_worker_adapter_verification(db_path, "codex", verified=True, evidence={"ok": True})

    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="codex",
        model="gpt-5.1-codex",
        session_api_key="sk_session",
        proxy_url="http://127.0.0.1:8000/v1",
    )

    assert result.passed is True
    assert result.reasons == []
    assert result.launchable is True


def test_launch_guardrails_block_observed_only_tracking(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "codex",
        workdir=str(tmp_path),
        config={"command": "codex"},
        supported_models=["gpt-5.1-codex"],
    )
    db.mark_worker_adapter_verification(
        db_path,
        "codex",
        verified=True,
        evidence={"tracking_mode": "observed_only", "tracking_authoritative": False},
    )

    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="codex",
        model="gpt-5.1-codex",
        session_api_key="sk_session",
        proxy_url="http://127.0.0.1:8000/v1",
    )

    assert result.passed is False
    assert "Observed-only Worker tracking cannot launch governed tasks." in result.reasons


def test_launch_guardrails_return_human_readable_failures(tmp_path):
    db_path = tmp_path / "harness.db"
    missing_workdir = tmp_path / "missing"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "claude_code",
        workdir=str(missing_workdir),
        config={},
        supported_models=["claude-3-5-sonnet-latest"],
    )

    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="claude_code",
        model="gpt-5.1-codex",
        session_api_key="",
        proxy_url="",
    )

    assert result.passed is False
    assert result.launchable is False
    assert "Worker adapter is not configured." in result.reasons
    assert "Token tracking has not been verified for this adapter." in result.reasons
    assert "Worker adapter workdir does not exist." in result.reasons
    assert "Selected model is not supported by this adapter." in result.reasons
    assert "Session API key is required for harness proxy token tracking." not in result.reasons
    assert "Harness proxy URL is required for adapter launch." not in result.reasons


def test_launch_guardrails_native_usage_does_not_require_proxy_credentials(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(tmp_path),
        config={"command": "opencode"},
        supported_models=["opencode/gpt-5.1"],
    )
    db.mark_worker_adapter_verification(
        db_path,
        "opencode",
        verified=True,
        evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
    )

    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        session_api_key=None,
        proxy_url=None,
    )

    assert result.passed is True
    assert result.reasons == []


def test_launch_guardrails_require_discovered_worker_model(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(tmp_path),
        config={"command": "opencode"},
        supported_models=[],
    )
    db.mark_worker_adapter_verification(
        db_path,
        "opencode",
        verified=True,
        evidence={"tracking_mode": "native_usage", "tracking_authoritative": True},
    )

    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        session_api_key=None,
        proxy_url=None,
    )

    assert result.passed is False
    assert "No discovered Worker models are available for this adapter." in result.reasons


def test_launch_guardrails_require_budget_authoritative_tracking(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(tmp_path),
        config={"command": "opencode"},
        supported_models=["opencode/gpt-5.1"],
    )
    db.mark_worker_adapter_verification(
        db_path,
        "opencode",
        verified=True,
        evidence={"tracking_mode": "native_usage", "tracking_authoritative": False},
    )

    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        session_api_key=None,
        proxy_url=None,
    )

    assert result.passed is False
    assert "Budget-authoritative Worker tracking has not been verified for this adapter." in result.reasons


def test_launch_guardrails_reject_observed_only_for_board_launch(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)
    db.update_worker_adapter(
        db_path,
        "opencode",
        workdir=str(tmp_path),
        config={"command": "opencode"},
        supported_models=["opencode/gpt-5.1"],
    )
    db.mark_worker_adapter_verification(
        db_path,
        "opencode",
        verified=True,
        evidence={"tracking_mode": "observed_only", "tracking_authoritative": False},
    )

    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="opencode",
        model="opencode/gpt-5.1",
        session_api_key=None,
        proxy_url=None,
    )

    assert result.passed is False
    assert "Observed-only Worker tracking cannot launch governed tasks." in result.reasons


def test_launch_guardrails_fail_for_unknown_adapter(tmp_path):
    db_path = tmp_path / "harness.db"
    db.init_db(db_path)

    result = evaluate_launch_guardrails(
        db_path,
        adapter_id="missing",
        model="claude-3-5-sonnet-latest",
        session_api_key="sk_session",
        proxy_url="http://127.0.0.1:8000/v1",
    )

    assert result.passed is False
    assert result.reasons == ["Worker adapter not found."]
