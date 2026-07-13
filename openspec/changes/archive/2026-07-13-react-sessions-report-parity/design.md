## Context

The canonical `/sessions` and `/sessions/{session_id}` routes currently render Jinja from `portal.sessions_index` and `portal.session_report_view`. The report context already composes the authoritative artifact, evidence summary, normalized token breakdown, Worker token components, related Agent Review, guardrail snapshots, redacted Worker events, alarms, checkpoints, and Repo Context Brief. React currently owns only `/app`, project workspaces, and project boards; its sidebar links Sessions by full-page navigation.

This slice migrates the list and report together because they form one evidence workflow. FastAPI remains authoritative, the existing Jinja rendering remains a missing/partial-build fallback, and no persistence or mutation contract changes.

## Goals / Non-Goals

**Goals:**

- Own canonical `/sessions` and `/sessions/{session_id}` in React when the complete build is available.
- Preserve information parity with both Jinja surfaces through authenticated, allowlisted, bounded projections derived from shared backend context.
- Keep summaries first and raw evidence secondary without removing token, timeline, repo-context, alarm, checkpoint, or Agent Review audit paths.
- Refresh active lists automatically without rewriting a report while it is being read.
- Preserve auth, missing-session behavior, direct deep links, and missing/partial-build Jinja fallback.

**Non-Goals:**

- No new mutations, schema migration, websocket/SSE transport, generic event bus, or generalized real-time Portal contract.
- No token-accounting, evidence-persistence, Worker Adapter, guardrail, alarm, checkpoint, or Agent Review behavior changes.
- No `/app/sessions` aliases, Jinja deletion, login migration, mobile acceptance scope, or visual redesign.
- No arbitrary raw artifact JSON in browser responses.

## Decisions

### 1. Reuse one backend context per surface

Extract shared backend builders from the current Jinja handlers: one newest-first Sessions index builder and one Session Report builder. Jinja consumes those builders unchanged; React projection helpers consume the same results. Calculations for budget zone, session kind, review state, token totals/categories/components, related Agent Review, and evidence sanitization remain server-side.

Alternative: call the existing `/session/{id}/artifact` endpoint or duplicate Jinja calculations in React. Rejected because the artifact is broad, the route has a different contract, and either option would expose internals or create split authority.

### 2. Canonical GETs select React only for a complete build

The existing `/sessions` and `/sessions/{session_id}` handlers first enforce Portal auth, then use the existing index-plus-referenced-assets validator. A complete build returns the React index for either canonical route. Missing or partial assets execute the current Jinja response path. Unknown session IDs remain `404` in both modes: the report route verifies existence before returning the shell, so a valid build does not turn unknown IDs into a client-only success. No `/app/sessions` route is added.

Alternative: always serve React and display a boot error when assets are missing. Rejected because each migrated canonical surface must preserve useful Jinja fallback during staged migration.

### 3. Use authenticated read-only handoff patterns

- `GET /api/sessions?offset=<n>&limit=<n>` returns newest-first compact rows. Default limit is 50; maximum is 100. It also reports total rows, whether more rows exist, whether any session is active, and `poll_after_ms` (`5000` only while active, otherwise `null`).
- `GET /api/sessions/{session_id}/report` returns summary state plus the first bounded page of each report collection.
- `GET /api/sessions/{session_id}/evidence/{collection_id}?offset=<n>&limit=<n>` pages an allowlisted collection. Fixed ids are `token-log`, `zone-timeline`, `worker-timeline`, `repo-context`, `alarms`, `checkpoints`, and `agent-review-findings`. Nested Repo Context ids are `repo-documents-{zero-based-run-index}` and `repo-manifests-{zero-based-run-index}`. Any other id returns `404`; ids are never interpreted as table names, metadata paths, or file paths.
- `GET /api/sessions/{session_id}/text/{text_id}` returns complete redacted `text/plain; charset=utf-8` only for a `full_href` emitted by the bounded projection. Fixed ids are `task`, `selected-project`, `launch-target`, `result`, `agent-review-summary`, and `agent-review-error`. Dynamic ids are exactly `token-raw-{ordinal}`, `worker-detail-{ordinal}`, `repo-text-{run-ordinal}`, `checkpoint-detail-{ordinal}`, and `agent-review-finding-{ordinal}` where ordinals are canonical non-negative decimal integers (`0` or no leading zero). Unknown ids return `404`. Responses use `Cache-Control: no-store` and never return unredacted source values.
- `GET /api/sessions/{session_id}/freshness` returns only `session_id`, `status`, `active`, `version`, and `last_evidence_at`.

All use `require_portal_auth` and return `404` with sanitized `session not found` detail for an unknown id. Query validation is deterministic: malformed integers, `offset < 0`, `limit < 1`, or `limit` above the endpoint maximum return FastAPI `422`; values are never silently clamped. They never return `session_key_hash`, `guardrail_overrides`, command environment, adapter configuration, secret values, unredacted headers/credentials, raw DB rows, or unknown metadata keys.

### 4. Fixed browser types, projections, bounds, and ordering

Sanitize/redact before preview truncation. Wrong container/scalar types become typed empty values rather than `500`.

**Shared scalar contracts**

| Contract | Exact type/default |
|---|---|
| required string | string; malformed/missing becomes `""`; sanitize then truncate to field bound |
| optional string/timestamp | string or `null`; malformed/empty becomes `null`; sanitize then truncate |
| boolean | JSON boolean; malformed becomes `false` |
| count/token/component value | JSON integer `>= 0`; booleans, malformed, and negative values become `0` |
| nullable non-negative integer | JSON integer `>= 0` or `null`; missing, boolean, malformed, and negative values become `null` |
| cost | finite JSON number `>= 0` or `null`; booleans, malformed, negative, NaN, and infinity become `null` |
| bounded text | exactly `preview`, `truncated`, `full_href`; preview is a sanitized string, truncated is boolean, and full_href is `null` unless omitted sanitized text is available through the generated same-session text endpoint |
| page | exactly `items`, `pagination`; pagination is exactly `offset`, `limit`, `total`, `has_more`, `next_href` with non-negative integers, boolean, and generated same-session URL or `null` |

**Sessions response** has exactly `sessions`, `pagination`, `has_active`, and `poll_after_ms`. Each row has exactly `id`, `kind`, `task_preview`, `model`, `status`, `active`, `token_totals`, `evidence_counts`, `current_zone`, `alarm_count`, and `report_href`. Token totals have `prompt_tokens`, `completion_tokens`, `total_tokens`; evidence counts have `worker_runs`, `worker_events`, `failed_checkpoints`. Pagination has `offset`, `limit`, `total`, `has_more`. Strings use id 128, kind 32, task preview 240, model 200, status 64, zone 32. `poll_after_ms` is integer `5000` or `null`; `report_href` is generated only as `/sessions/{encoded-id}`. Sessions order by `started_at DESC, id DESC`.

**Report response** has exactly `session`, `summary`, `tokens`, `zone_timeline`, `worker_timeline`, `repo_context_briefs`, `alarms`, `checkpoints`, `related_agent_review`, `freshness`, and `links`.

- `session`: exactly `id`, `kind`, `task`, `model`, `status`, `started_at`, `active`. `task` is bounded text with 20,000-character preview; id 128, kind 32, model 200, status 64, started-at 64.
- `summary`: exactly `selected_project`, `launch_target`, `adapter_id`, `worker_model`, `tracking_mode`, `status`, `result`, `requires_review`, `missing_labels`, `evidence_counts`. `selected_project` is bounded text with 1,000 preview; `launch_target` and `result` are bounded text with 4,000 previews. Adapter/model/tracking/status are required strings bounded 200/200/64/64. Missing labels are at most 20 generated strings × 500 and cannot omit source evidence. Evidence counts are exactly `alarms`, `checkpoints`, `failed_checkpoints`, `worker_runs`, `worker_events`, `error_events` using count rules.
- `tokens`: exactly `provider_totals`, `normalized`, `worker_components`, `log`. Provider totals use three canonical non-negative integer keys. Normalized has non-negative `total_tokens` and fixed non-negative `by_category` keys `control_plane`, `task_breakdown`, `worker_execution`, `adapter_verification`, `reporting_summary`, `other`. Worker components has boolean `available`, page-free `items`, nullable cost, and non-negative `turn_count`; at most 20 canonical component items exist, each exactly `key` (64 string), `label` (200 string), `value` (non-negative integer). `log` is the first `token-log` page; each item is exactly `usage_kind`, `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost`, `raw_usage`, with raw usage as bounded text (20,000 preview plus full continuation).
- `zone_timeline`: first page; each item exactly `zone`, `max_tokens`, `created_at`. Zone/timestamp are required/optional strings bounded 64; max tokens follows the nullable non-negative integer rule. Order: snapshot database id ASC.
- `worker_timeline`: first page; each item exactly `created_at`, `level`, `layer`, `kind`, `title`, `detail_summary`, `detail`. Strings are bounded 64/64/64/64/200/1,000; detail is bounded text with 20,000 preview and continuation. Order: `created_at ASC, id ASC`.
- `repo_context_briefs`: first page; each item exactly `worker_run_id`, `documents`, `manifests`, `text`. Id is 128 string; documents and manifests are first page wrappers with generated nested collection ids, default 50/max 100; document items are exactly `path` (1,000 string), manifest items are 1,000 strings, and stored list order plus ordinal is stable. Text is bounded text with 40,000 preview and continuation. Brief order: `worker_run.created_at ASC, worker_run.id ASC`.
- `alarms`: first page; each item exactly `id`, `type`, `severity`, `recommended_action`, `created_at`, bounded 128/200/64/2,000/64. Order: `created_at ASC, id ASC`.
- `checkpoints`: first page; each item exactly `name`, `passed`, `details`; name 200 required string, passed boolean, details bounded text with 20,000 preview and continuation. Order: checkpoint database id ASC.
- `related_agent_review`: `null` or exactly `status`, `recommendation`, `summary`, `model`, `reviewed_at`, `review_session_id`, `review_session_href`, `review_total_tokens`, `error`, `findings`. Status/recommendation/model/reviewed_at/review_session_id are optional strings with 200/200/200/64/128 bounds; summary/error are `null` or bounded text with 4,000 previews and continuation; review href is `null` unless a non-empty session id generates `/sessions/{encoded-id}`; review total tokens follows the nullable non-negative integer rule; findings is the first `agent-review-findings` page, each item bounded text with 4,000 preview and continuation, preserving stored list order.
- `freshness`: exact contract below.
- `links`: exactly generated `sessions_href: /sessions` and `self_href: /sessions/{encoded-id}`.

Top-level collection defaults/maxima are 50/100 for token log, zone timeline, alarms, checkpoints, and Agent Review findings; 100/200 for Worker timeline; 20/100 for Repo Context briefs. Token log and checkpoint order by database id ASC. React appends pages only after explicit `Load more`, so every list and nested source entry remains reachable. Every omitted text byte is reachable only through the emitted authenticated full-text continuation. Persisted evidence is unchanged.

### 5. Freshness is an exact append/status contract, not a report replay

Freshness detects session status transitions; appended token turns, guardrail snapshots, alarms, checkpoint rows, Worker Runs, and Worker Run events; plus a digest of each Worker's projected mutable result scalars (`status`, `started_at`, `completed_at`, `returncode`, `error_type`, and `error_message`). The opaque `version` is exactly a lowercase 64-character SHA-256 hex digest over those normalized revision markers. `session_id` is a required string bounded 128; `status` required string bounded 64; `active` boolean; `last_evidence_at` optional string bounded 64, defaulting to session start when no later marker exists.

In-place edits to raw evidence fields or related Agent Review task metadata without one of those revision markers are explicitly outside freshness notification semantics; reopening or explicit Refresh still loads current authoritative state. This is acceptable because polling occurs only for active/running sessions and Agent Review is a post-run workflow. Tests cover this boundary rather than promising detection of every arbitrary database edit.

The report builder reads one consistent database snapshot and computes its embedded version from that snapshot. The lightweight endpoint computes the same normalized marker tuple in one read transaction. It never serializes report evidence or secrets.

Alternative: poll or hash the complete report, or add a schema-wide revision counter. Rejected because this slice is read-only/no-migration and should not repeatedly transfer or scan large raw evidence.

### 6. Polling is narrow and operator-controlled

The Sessions view polls every five seconds only when `has_active` is true, replaces list state after successful responses, announces failures without clearing current rows, and stops on unmount or when no active/running session remains.

An active Session Report polls only freshness every five seconds. A changed version shows `New session evidence available` with an explicit Refresh button. It does not replace report state automatically. Refresh fetches the report and replaces it only on success. Polling stops when freshness reports a terminal status; a final changed version still leaves the notice visible. Failed polls preserve current evidence and expose a retryable sanitized message.

Alternative: live-update sections independently. Rejected because it causes reading-position and disclosure-state churn and establishes a broader synchronization contract.

### 7. React preserves report hierarchy and navigation

The Sessions list keeps scan fields in a semantic table with pagination and empty/error/loading states. The report starts with session/launch/review summary, then token totals/categories/components; raw token usage, timelines, Repo Context Brief, alarms, checkpoints, and findings use semantic sections and native `<details>`/bounded raw regions. Missing evidence remains explicit. Keyboard focus, visible focus, headings, table semantics, non-color-only statuses, and `aria-live` notices are required.

The React sidebar marks Sessions active on both canonical routes. Links from Dashboard, Board, Agent Review, Alarms, and Task Breakdown continue using canonical `/sessions/...` URLs and therefore enter React when built or Jinja when not.

## Risks / Trade-offs

- **[Large report payload despite caps]** → Keep compact summary first, cap/redact every collection/string, and poll only freshness.
- **[Jinja/React drift]** → Extract shared context builders and test parity fields against identical seeded state.
- **[Evidence changes during a read]** → Never auto-replace report data; use an explicit freshness notice and Refresh.
- **[Unknown session briefly serves shell]** → Verify session existence before shell response and keep backend/API `404` authoritative.
- **[Projection caps hide evidence]** → Every capped collection is pageable, every capped evidence string emits truncation plus authenticated full-text continuation, and tests prove overflow remains reachable without Jinja.
- **[Polling load]** → Five-second interval, active-only stop rules, lightweight aggregate freshness query, cleanup on unmount.
- **[Dirty worktree attribution]** → Limit implementation to the named route/frontend/test surfaces and do not alter archived prior changes.

## Migration Plan

1. Add failing auth, exact-shape/bounds/redaction, fallback, unknown-id, parity, and freshness tests.
2. Extract shared list/report context and add bounded projections plus freshness helper/endpoints.
3. Add canonical build-aware route handoff while retaining the same Jinja fallback path.
4. Add React routes/views/components, active sidebar state, polling, explicit refresh, and accessibility behavior.
5. Run frontend checks, focused Portal tests, full pytest, strict OpenSpec validation, browser smoke for built and fallback modes, and independent review.

Rollback is route-local: stop selecting the React shell for canonical Sessions routes while leaving Jinja handlers and persisted data unchanged.

## Open Questions

None. The migration plan settles route ownership, fallback, projection, polling, and non-goals for this slice.
