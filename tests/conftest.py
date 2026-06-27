import pytest


@pytest.fixture(autouse=True)
def _test_portal_token(monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", "test-portal-token")
