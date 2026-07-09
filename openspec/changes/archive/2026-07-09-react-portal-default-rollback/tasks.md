## 1. Roll back the default landing in the backend

- [x] 1.1 In `src/agile_ai_htb/routes/portal.py`, remove the `if _react_shell.react_build_available(): return "/app"` branch from `_default_portal_landing` so it resolves to `/projects/{first-connected}` when projects exist and `/projects` when none do, regardless of whether the React build is present.
- [x] 1.2 Delete the `react_build_available()` function from `src/agile_ai_htb/routes/react_shell.py`. Confirmed no other caller references it (only `_default_portal_landing` did). Left `_react_index()`, `_referenced_assets_available()`, `_MISSING_BUILD_HTML`, the `/app` route, the asset route, and all `/api/*` JSON endpoints unchanged.
- [x] 1.3 Removed the now-unused `from agile_ai_htb.routes import react_shell as _react_shell` import from `portal.py`; no remaining `_react_shell.` usage exists in that file.

## 2. Update tests to match the rolled-back default

- [x] 2.1 In `tests/portal/test_react_shell.py`, flipped `test_landing_prefers_react_shell_when_built` → `test_landing_uses_jinja_even_when_react_built`, asserting `/projects` instead of `/app`.
- [x] 2.2 Flipped `test_authenticated_root_prefers_react_shell_when_built` → `test_authenticated_root_uses_jinja_even_when_react_built`, asserting `/projects` instead of `/app`.
- [x] 2.3 Flipped `test_login_redirects_to_react_shell_when_built` → `test_login_redirects_to_jinja_even_when_react_built`, asserting `/projects` instead of `/app`. Cookie-set assertion retained.
- [x] 2.4 Added `test_built_react_and_valid_cookie_lands_on_jinja_not_app` — builds assets, connects a project, performs real login, asserts root redirects to `/projects/{id}` and the rendered Jinja project page returns 200 with `<html`.
- [x] 2.5 Already-correct tests stayed green: `test_landing_falls_back_to_jinja_when_build_missing`, `test_authenticated_root_falls_back_to_jinja_when_build_missing`, `test_login_falls_back_to_jinja_when_build_missing`, `test_partial_react_build_falls_back_without_blank_shell`, `test_react_shell_served_when_built`, `test_react_shell_reports_missing_build`, `test_react_json_endpoints_require_auth`, `test_react_projects_endpoint_*`, `test_react_workspace_state_reuses_project_helpers`, `test_react_board_state_*`, `test_jinja_project_pages_remain_available`.

## 3. Verify

- [x] 3.1 `openspec validate react-portal-default-rollback --strict` → "Change 'react-portal-default-rollback' is valid"
- [x] 3.2 `npm --prefix frontend run check` → 38 modules transformed, built in 200ms
- [x] 3.3 `uv run pytest tests/portal/test_react_shell.py -q` → 19 passed, 1 warning
- [x] 3.4 `uv run pytest -q` → 607 passed, 1 warning
- [x] 3.5 `git diff --check` → exit 0, clean
- [x] 3.6 All task checkboxes updated to `- [x]` after the corresponding verification passed.