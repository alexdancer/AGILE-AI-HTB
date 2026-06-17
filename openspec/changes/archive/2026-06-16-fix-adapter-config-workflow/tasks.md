## 1. Workers page — workdir and default controls

- [x] 1.1 Add `POST /settings/workers/{adapter_id}/configure` route in `routes/portal.py` accepting `workdir` and `is_default` form fields
- [x] 1.2 Add workdir form to each adapter card in `templates/workers.html`
- [x] 1.3 Add "Set as default" button to each adapter card in `templates/workers.html`
- [x] 1.4 Add `POST /settings/workers/{adapter_id}/configure` form handling with redirect back to `/settings/workers`

## 2. Workers page — diagnostics for all adapters

- [x] 2.1 Remove the `if adapter.get("id") == "opencode"` gate in `routes/portal.py` worker_settings route
- [x] 2.2 Call `detect_worker_adapter()` for every adapter, store result in `adapter["config"]["_diagnostics"]`
- [x] 2.3 Cache diagnostics in DB via `db.update_worker_adapter()` with 5-minute TTL check
- [x] 2.4 Add "Refresh diagnostics" button per adapter card in `templates/workers.html`
- [x] 2.5 Add `POST /settings/workers/{adapter_id}/refresh-diagnostics` route that forces re-detection

## 3. Board — adapter and model selectors

- [x] 3.1 Pass adapter list to board template context in `routes/portal.py` board route
- [x] 3.2 Add adapter `<select>` dropdown to board launch form in `templates/board.html`
- [x] 3.3 Add model `<select>` dropdown to board launch form, initially populated from default adapter's models
- [x] 3.4 Add inline `<script>` to filter model dropdown when adapter selection changes
- [x] 3.5 Update `POST /tasks/{task_id}/launch` form to include `adapter_id` and `model` fields

## 4. Board — always-visible launch button with error feedback

- [x] 4.1 Remove `has_verified_worker_adapter` gate from launch button visibility in `templates/board.html`
- [x] 4.2 Add error banner rendering to board template (reads `request.query_params.get("error")`)
- [x] 4.3 Update `launch_task_endpoint` in `routes/tasks.py` to redirect with `?error=` on `TaskLaunchBlocked`
- [x] 4.4 Pass adapter list and verified status as context rather than gating on it

## 5. Tests

- [x] 5.1 Add test: workdir form POST updates adapter and redirects to workers page
- [x] 5.2 Add test: default adapter switching clears previous default
- [x] 5.3 Add test: diagnostics shown for non-OpenCode adapters
- [x] 5.4 Add test: board launch form includes adapter and model selectors
- [x] 5.5 Add test: launch with unverified adapter shows error banner on board redirect
- [x] 5.6 Add test: launch button visible when no verified adapter exists
