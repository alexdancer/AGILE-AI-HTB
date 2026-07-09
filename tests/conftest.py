import pytest


@pytest.fixture(autouse=True)
def _test_portal_token(monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", "test-portal-token")


@pytest.fixture(autouse=True)
def _react_build_absent(tmp_path, monkeypatch):
    # The built React shell lives in a git-ignored directory, so its presence
    # depends on the developer's machine. Pin every test to "build absent";
    # tests that need the built shell monkeypatch react_build_dir themselves.
    from agile_ai_htb.routes import react_shell

    monkeypatch.setattr(react_shell, "react_build_dir", lambda: tmp_path / "no-react-build")
