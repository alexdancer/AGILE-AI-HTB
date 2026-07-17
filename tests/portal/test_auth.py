from pathlib import Path

from foreman_ai_hq import db
from foreman_ai_hq.routes import react_shell
from tests.portal.helpers import PORTAL_TOKEN, _client, _portal_headers


def _build_react_assets(tmp_path):
    # Matches tests/portal/test_react_shell.py::_build_react_assets. Duplicated
    # locally rather than imported because this file is scoped to only touch
    # tests/portal/test_auth.py.
    build_dir = tmp_path / "react_build"
    (build_dir / "assets").mkdir(parents=True)
    (build_dir / "index.html").write_text(
        '<!doctype html><div id="root"></div>'
        '<script type="module" src="/static/react/assets/main.js"></script>',
        encoding="utf-8",
    )
    (build_dir / "assets" / "main.js").write_text(
        "console.log('react shell');", encoding="utf-8"
    )
    return build_dir


def test_portal_routes_require_operator_bearer_token(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path) as client:
        started = client.post(
            "/session/start",
            headers={"Authorization": "Bearer test-portal-token"},
            json={"task_description": "Secured portal", "model": "claude-haiku"},
        ).json()

        # /board is a redirect shim onto a project board (303), not a rendered
        # page; /dashboard and /sessions/{id} are React-shell routes that need
        # a build present to answer 200 instead of the missing-build 503.
        expected_status = {
            "/dashboard": 200,
            "/board": 303,
            f"/sessions/{started['session_id']}": 200,
        }
        for path, ok_status in expected_status.items():
            assert client.get(path).status_code == 401
            assert client.get(path, headers={"Authorization": "Bearer wrong"}).status_code == 401
            response = client.get(path, headers=_portal_headers(), follow_redirects=False)
            assert response.status_code == ok_status

def test_portal_login_sets_signed_http_only_cookie_and_logout_clears_it(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN}, follow_redirects=False)

        assert login.status_code == 303
        # Login now always lands on the React dashboard shell; the retired
        # Jinja /projects landing no longer exists (final-jinja-retirement,
        # design.md Decision 1: "Landing stops checking").
        assert login.headers["location"] == "/dashboard"
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
    build_dir = _build_react_assets(tmp_path)
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: build_dir)
    with _client(tmp_path, portal_auth_required=False) as client:
        root = client.get("/", follow_redirects=False)
        login = client.get("/login", follow_redirects=False)
        dashboard = client.get("/dashboard")

    assert root.status_code == 307
    # Root and /login both bounce to the React dashboard shell now; the
    # retired Jinja /projects landing no longer exists.
    assert root.headers["location"] == "/dashboard"
    assert login.status_code == 307
    assert login.headers["location"] == "/dashboard"
    assert dashboard.status_code == 200
    assert "Logout" not in dashboard.text


def test_portal_auth_disabled_logout_clears_cookie_and_returns_to_landing(tmp_path, monkeypatch):
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_TOKEN", raising=False)
    with _client(tmp_path, portal_auth_required=False) as client:
        logout = client.post("/logout", follow_redirects=False)

    assert logout.status_code == 303
    # Same landing consolidation as above: logout with auth disabled now
    # returns to /dashboard, not the retired /projects Jinja page.
    assert logout.headers["location"] == "/dashboard"
    assert "foreman_ai_hq_portal=\"\"" in logout.headers["set-cookie"]

def test_portal_login_always_redirects_to_dashboard_regardless_of_recent_project(tmp_path, monkeypatch):
    # Previously this asserted login redirected to the most recently touched
    # project's page. final-jinja-retirement design.md Decision 1 collapsed
    # that build-aware landing logic (`_default_portal_landing`), so login now
    # always lands on /dashboard no matter which project was last connected.
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    db.init_db(tmp_path / "harness.db")
    db.upsert_connected_project(
        tmp_path / "harness.db",
        name="first-project",
        root_path=str(tmp_path / "first-project"),
        profile={},
        capability={},
    )
    db.upsert_connected_project(
        tmp_path / "harness.db",
        name="second-project",
        root_path=str(tmp_path / "second-project"),
        profile={},
        capability={},
    )

    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN}, follow_redirects=False)

    assert login.status_code == 303
    assert login.headers["location"] == "/dashboard"

def test_portal_rejects_tampered_or_expired_login_cookie(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        # Don't follow the post-login redirect: this test is about the cookie,
        # not the destination page, and following it would hit /dashboard's
        # missing-build 503 rather than the retired Jinja 200.
        login = client.post("/login", data={"token": PORTAL_TOKEN}, follow_redirects=False)
        assert login.status_code == 303
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
    assert response.headers.get("content-type", "").startswith("text/html")
    assert "<!doctype html>" in response.text.lower()
    assert "Invalid portal token" in response.text
    assert "wrong" not in response.text


def test_failed_login_uses_same_error_for_all_rejection_causes(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        wrong_token = client.post("/login", data={"token": "wrong"})
        empty_token = client.post("/login", data={"token": ""})
        monkeypatch.delenv("TOKEN_TRACKER_PORTAL_TOKEN", raising=False)
        absent_token = client.post("/login", data={"token": "any"})

    assert wrong_token.status_code == 401
    assert empty_token.status_code == 401
    assert absent_token.status_code == 401
    assert "Invalid portal token" in wrong_token.text
    assert wrong_token.text == empty_token.text == absent_token.text


def test_login_without_token_field_is_an_ordinary_rejection(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        missing_field = client.post("/login", data={})
        wrong_token = client.post("/login", data={"token": "wrong"})

    # An absent field must not be distinguishable from an incorrect token, so it
    # is a rejection rather than a 422 field-validation response.
    assert missing_field.status_code == 401
    assert missing_field.headers.get("content-type", "").startswith("text/html")
    assert missing_field.text == wrong_token.text


def test_login_does_not_reuse_the_synthetic_data_banner(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    with _client(tmp_path) as client:
        response = client.get("/login")

    # `demo-banner` marks fabricated task data on the board; branding must not
    # borrow that warning treatment.
    assert "demo-banner" not in response.text
    assert "Foreman AI HQ portal · operator-controlled budget governance" in response.text


def test_login_renders_standalone_without_chrome(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    db.init_db(tmp_path / "harness.db")
    db.upsert_connected_project(
        tmp_path / "harness.db",
        name="secret-project",
        root_path=str(tmp_path / "secret-project"),
        profile={},
        capability={},
    )
    with _client(tmp_path) as client:
        response = client.get("/login")

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/html")
    assert "Operator login" in response.text
    assert "sidebar" not in response.text.lower()
    assert "project-list" not in response.text.lower()
    assert "secret-project" not in response.text
    assert "Logout" not in response.text
    assert "{% extends" not in response.text


def test_login_template_has_no_template_dependencies():
    template = Path(__file__).resolve().parents[2] / "src" / "foreman_ai_hq" / "templates" / "login.html"
    source = template.read_text()
    assert "{% extends" not in source
    assert "{% include" not in source


def test_portal_login_redirects_to_build_aware_landing_when_react_present(tmp_path, monkeypatch):
    from foreman_ai_hq.routes import react_shell

    monkeypatch.setenv("TOKEN_TRACKER_PORTAL_TOKEN", PORTAL_TOKEN)
    real_build_dir = Path(__file__).resolve().parents[2] / "src" / "foreman_ai_hq" / "static" / "react"
    monkeypatch.setattr(react_shell, "react_build_dir", lambda: real_build_dir)

    with _client(tmp_path) as client:
        login = client.post("/login", data={"token": PORTAL_TOKEN}, follow_redirects=False)

    assert login.status_code == 303
    assert login.headers["location"] == "/dashboard"
    cookie = login.headers["set-cookie"]
    assert "foreman_ai_hq_portal=" in cookie
    assert "HttpOnly" in cookie


def test_auth_disabled_login_never_renders_token_form(tmp_path, monkeypatch):
    monkeypatch.delenv("TOKEN_TRACKER_PORTAL_TOKEN", raising=False)
    with _client(tmp_path, portal_auth_required=False) as client:
        response = client.get("/login", follow_redirects=False)

    assert response.status_code == 307
    # Login bounces to /dashboard now, not the retired /projects Jinja page.
    assert response.headers["location"] == "/dashboard"
    assert "Portal token" not in response.text
