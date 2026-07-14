import json

from foreman_ai_hq.native_cli_diagnostics import native_cli_diagnostic, redact_native_cli_text


def test_claude_code_login_failure_from_jsonl_is_actionable_and_redacted():
    stdout = json.dumps(
        {
            "type": "error",
            "message": "Not logged in · Please run /login token=sk_sess_DEMO_2099_SECRET",
            "is_error": True,
        }
    )

    diagnostic = native_cli_diagnostic(
        adapter_id="claude_code",
        adapter_kind="claude_code",
        stdout=stdout,
        stderr="",
        returncode=1,
    )

    assert diagnostic is not None
    assert diagnostic["code"] == "claude_code_not_logged_in"
    assert diagnostic["summary"] == "Not logged in · Please run /login"
    assert diagnostic["setup_href"] == "/settings/workers"
    assert "/login" in diagnostic["next_action"]
    assert "sk_sess_DEMO_2099_SECRET" not in str(diagnostic)
    assert "***REDACTED***" in diagnostic["detail"]


def test_codex_trusted_directory_failure_from_stderr_is_actionable():
    diagnostic = native_cli_diagnostic(
        adapter_id="codex",
        adapter_kind="codex",
        stdout="",
        stderr="Not inside a trusted directory and --skip-git-repo-check was not specified.",
        returncode=1,
    )

    assert diagnostic is not None
    assert diagnostic["code"] == "codex_untrusted_directory"
    assert diagnostic["summary"] == "Not inside a trusted directory and --skip-git-repo-check was not specified."
    assert diagnostic["setup_href"] == "/settings/workers"
    assert "--skip-git-repo-check" in diagnostic["next_action"]


def test_trusted_directory_failure_is_only_classified_for_codex():
    diagnostic = native_cli_diagnostic(
        adapter_id="opencode",
        adapter_kind="opencode",
        stdout="",
        stderr="Not inside a trusted directory and --skip-git-repo-check was not specified.",
        returncode=1,
    )

    assert diagnostic is not None
    assert diagnostic["code"] == "native_cli_failure"


def test_shared_redaction_covers_plain_api_keys_and_bearer_tokens():
    redacted = redact_native_cli_text("api_key=abc123 Bearer abc.def password:letmein token=demo-token")

    assert "api_key=abc123" not in redacted
    assert "Bearer abc.def" not in redacted
    assert "password:letmein" not in redacted
    assert "token=demo-token" not in redacted
    assert redacted.count("***REDACTED***") == 4


def test_generic_cli_failure_is_bounded_and_redacted():
    noisy = "API_KEY=super-secret " + ("failure detail " * 100)

    diagnostic = native_cli_diagnostic(
        adapter_id="opencode",
        adapter_kind="opencode",
        stdout=noisy,
        stderr="",
        returncode=2,
    )

    assert diagnostic is not None
    assert diagnostic["code"] == "native_cli_failure"
    assert diagnostic["summary"].startswith("OpenCode CLI failed:")
    assert len(diagnostic["summary"]) <= 180
    assert len(diagnostic["detail"]) <= 500
    assert "super-secret" not in str(diagnostic)
    assert "***REDACTED***" in str(diagnostic)
