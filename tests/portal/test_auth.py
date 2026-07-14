from foreman_ai_hq import db
from tests.portal.helpers import PORTAL_TOKEN, _client, _portal_headers

def test_portal_routes_require_operator_bearer_token(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": "Secured portal", "model": "claude-haiku"},
        ).json()

        for path in ["/dashboard", "/board", f"/sessions/{started['session_id']}"]:
            assert client.get(path).status_code == 401
            assert client.get(path, headers={"Authorization": "Bearer wrong"}).status_code == 401
            assert client.get(path, headers=_portal_headers()).status_code == 200

def test_portal_login_sets_signed_http_only_cookie_and_logout_clears_it(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN}, follow_redirects=False)

        assert login.status_code == 303
        assert login.headers["location"] == "/projects"
        cookie = login.headers["set-cookie"]
        assert "foreman_ai_hq_portal=" in cookie
        assert "HttpOnly" in cookie
        assert "SameSite=lax" in cookie
        assert "Max-Age=43200" in cookie
        assert "Secure" not in cookie

        assert client.get("/dashboard").status_code == 200

        logout = client.post("/logout", follow_redirects=False)
        assert logout.status_code == 303
        assert logout.headers["location"] == "/login"
        assert "foreman_ai_hq_portal=\"\"" in logout.headers["set-cookie"]
        assert client.get("/dashboard").status_code == 401


def test_portal_auth_disabled_opens_local_pages_without_token(tmp_path, monkeypatch):
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_TOKEN", raising=False)
    with _client(tmp_path, portal_auth_required=False) as client:
        root = client.get("/", follow_redirects=False)
        login = client.get("/login", follow_redirects=False)
        dashboard = client.get("/dashboard")

    assert root.status_code == 307
    assert root.headers["location"] == "/projects"
    assert login.status_code == 307
    assert login.headers["location"] == "/projects"
    assert dashboard.status_code == 200
    assert "Logout" not in dashboard.text


def test_portal_auth_disabled_logout_clears_cookie_and_returns_to_landing(tmp_path, monkeypatch):
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_TOKEN", raising=False)
    with _client(tmp_path, portal_auth_required=False) as client:
        logout = client.post("/logout", follow_redirects=False)

    assert logout.status_code == 303
    assert logout.headers["location"] == "/projects"
    assert "foreman_ai_hq_portal=\"\"" in logout.headers["set-cookie"]

def test_portal_login_redirects_to_most_recent_project(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    db.init_db(tmp_path / "harness.db")
    db.upsert_connected_project(
        tmp_path / "harness.db",
        name="first-project",
        root_path=str(tmp_path / "first-project"),
        profile={},
        capability={},
    )
    recent = db.upsert_connected_project(
        tmp_path / "harness.db",
        name="second-project",
        root_path=str(tmp_path / "second-project"),
        profile={},
        capability={},
    )

    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN}, follow_redirects=False)

    assert login.status_code == 303
    assert login.headers["location"] == f"/projects/{recent['id']}"

def test_portal_rejects_tampered_or_expired_login_cookie(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN})
        assert login.status_code == 200
        signed_cookie = client.cookies.get("foreman_ai_hq_portal")
        assert signed_cookie is not None

        client.cookies.set("foreman_ai_hq_portal", signed_cookie + "tampered")
        assert client.get("/dashboard").status_code == 401

        from foreman_ai_hq.auth import sign_portal_cookie

        client.cookies.set("foreman_ai_hq_portal", sign_portal_cookie(PORTAL_TOKEN, max_age_seconds=-1))
        assert client.get("/dashboard").status_code == 401

def test_portal_login_rejects_wrong_token(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.post("/login", data={"token": "wrong"})

    assert response.status_code == 401

