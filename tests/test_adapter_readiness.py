from agile_ai_htb.adapter_readiness import evaluate_adapter_readiness


def _adapter(**overrides):
    adapter = {
        "id": "opencode",
        "kind": "opencode",
        "workdir": None,
        "config": {},
        "supported_models": [],
        "verification_status": "unverified",
        "verification_evidence": {},
    }
    adapter.update(overrides)
    return adapter


def test_adapter_readiness_reports_launchable_proxy_adapter(tmp_path):
    readiness = evaluate_adapter_readiness(
        _adapter(
            workdir=str(tmp_path),
            config={"command": "opencode"},
            supported_models=["opencode/gpt-5.1"],
            verification_status="verified",
            verification_evidence={"tracking_mode": "proxy_governed", "tracking_authoritative": True},
        ),
        model="opencode/gpt-5.1",
        session_api_key="sk_session",
        proxy_url="http://127.0.0.1:8000/v1",
        include_launch_credentials=True,
    )

    assert readiness.ui_launchable is True
    assert readiness.launchable_for_board is True
    assert readiness.budget_authoritative is True
    assert readiness.tracking.mode == "proxy_governed"
    assert readiness.reasons == []


def test_adapter_readiness_collects_tracking_and_configuration_reasons(tmp_path):
    readiness = evaluate_adapter_readiness(
        _adapter(
            workdir=str(tmp_path / "missing"),
            config={"command": "opencode"},
            supported_models=["opencode/gpt-5.1"],
            verification_status="verified",
            verification_evidence={"tracking_mode": "observed_only", "tracking_authoritative": False},
        ),
        model="unsupported-model",
        include_launch_credentials=True,
    )

    assert readiness.ui_launchable is False
    assert readiness.launchable_for_board is False
    assert readiness.budget_authoritative is False
    assert readiness.launchable_tracking is False
    assert readiness.reasons == [
        "Observed-only Worker tracking cannot launch governed tasks.",
        "Worker adapter workdir does not exist.",
        "Selected model is not supported by this adapter.",
    ]


def test_adapter_readiness_proxy_launch_requires_credentials(tmp_path):
    readiness = evaluate_adapter_readiness(
        _adapter(
            workdir=str(tmp_path),
            config={"command": "opencode"},
            supported_models=["opencode/gpt-5.1"],
            verification_status="verified",
            verification_evidence={"tracking_mode": "proxy_governed", "tracking_authoritative": True},
        ),
        model="opencode/gpt-5.1",
        include_launch_credentials=True,
    )

    assert readiness.ui_launchable is True
    assert readiness.launchable_for_board is False
    assert "Session API key is required for harness proxy token tracking." in readiness.reasons
    assert "Harness proxy URL is required for adapter launch." in readiness.reasons
