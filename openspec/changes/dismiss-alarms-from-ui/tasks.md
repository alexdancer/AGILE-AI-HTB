## 1. Tests

- [x] 1.1 Update Portal alarm tests to prove an open alarm card renders a Dismiss action, posting it resolves the alarm, and the alarm disappears from the default `/alarms` HTML view.
- [x] 1.2 Update API alarm tests to prove resolved/dismissed alarms remain available with `resolved=true` and existing JSON resolve response shape stays unchanged.

## 2. Portal behavior

- [x] 2.1 Add an HTML-safe Dismiss form/button for unresolved alarm cards that submits the existing continue/resolve action.
- [x] 2.2 Make alarm resolution handle browser form submissions with a redirect back to `/alarms` while preserving existing JSON API behavior.
- [x] 2.3 Remove the default "Recently resolved" alarm list from the main Alarms page so resolved alarms do not remain visible inbox clutter.

## 3. Verification

- [x] 3.1 Run targeted alarm tests: `uv run pytest tests/api/test_alarms.py tests/portal/test_alarms.py`.
- [x] 3.2 Run the full repo check: `uv run pytest`.
