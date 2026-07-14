## Context

Budget Settings is Phase 5 slice #5 of the React Portal parity migration and the first of the Settings group. The current surface is `templates/budget.html` served by `portal.py`:

- `GET /settings/budget` renders the caps form, today's counter, and a spend-authority reference from `_effective_budget_settings(...)`.
- `POST /settings/budget` calls `db.set_token_budget_settings(...)`; for HTML it `303`-redirects to `/setup`, and for non-HTML it already returns the saved dict.
- `POST /settings/budget/reset` calls `db.reset_daily_budget_counter(...)`; HTML redirects to `/settings/budget`, non-HTML returns the saved dict.

The migration already established the reusable pattern with the Sessions, Task Breakdown Review, Project Task History, and Alarms slices: an authenticated bounded JSON read in `react_shell.py`, content-negotiated action outcomes on the existing `portal.py` mutation routes, and a React view rendered inside the shell on the canonical URL with a build-aware Jinja fallback. This slice applies that same pattern to the simplest mutation surface so Control Plane, Worker, and Project Settings can copy it.

## Goals / Non-Goals

**Goals:**
- React owns `/settings/budget` when the complete build exists; Jinja renders it otherwise, at the same URL.
- An authenticated bounded budget-state JSON read reusing `_effective_budget_settings`.
- Content-negotiated sanitized JSON outcomes for save and reset, preserving HTML redirects.
- On-page inline outcome + authoritative refetch after save/reset; no forced `/setup` redirect for React; confirmation before reset. This is the pattern the remaining Settings slices inherit.

**Non-Goals:**
- No change to budget enforcement, cache-read exclusion, spend-authority buckets, or any token-accounting rule.
- No schema/database migration.
- No migration of Control Plane / Worker / Project Settings or Setup Overview.
- No deletion of `budget.html` (final Jinja-retirement change owns that).
- No mobile/narrow-screen redesign; no new design system.

## Decisions

- **Reuse existing routes; add one read.** Add a `GET`-style authenticated JSON endpoint in `react_shell.py` (e.g. `/api/settings/budget`) guarded by `require_portal_auth`, derived entirely from `_effective_budget_settings`. Do not add a new mutation route — extend the existing `POST /settings/budget` and `.../reset` handlers to return a sanitized envelope when the caller negotiates `application/json`.
- **Negotiation matches the Alarms slice.** Reuse the same content-negotiation helper approach already used for the alarm resolve and Restore outcomes rather than inventing new logic. Success envelope carries the saved authoritative state; the error envelope carries sanitized text only (bounded, no exception/stack detail).
- **Build-aware GET.** `GET /settings/budget` selects React vs Jinja using the shell's existing index-plus-referenced-assets validator (same helper the landing and Sessions/Task-Breakdown routes use). This is an ADDED per-surface requirement rather than editing the large landing requirement's route-ownership enumeration; the generic "Settings non-migrated" scenario still holds for the other three settings pages.
- **On-page mutation, no forced redirect.** The React view POSTs with `Accept: application/json`, shows inline success/error, then refetches the budget JSON. It does not optimistically trust submitted values and does not navigate to `/setup`. `Back to setup` stays an explicit anchor. Reset is destructive-adjacent (counter window) so it requires a confirmation dialog with correct focus handling.
- **Field contract.** JSON read exposes exactly: daily cap, per-session Worker cap, current-window used, current-window remaining, `budget_since`, last daily-usage reset timestamp. Absent values are typed `null`, never fabricated zeros — matching the existing helper's `or ''`/`is not none` handling in the template.

## Risks / Trade-offs

- **Route-ownership enumeration drift.** The landing requirement lists "Settings" as non-migrated. Adding a per-surface ADDED requirement for `/settings/budget` supersedes it for this one path; archive-time reconciliation can tidy the enumeration when the whole Settings group is migrated. Accepted to avoid rewriting a large requirement mid-migration.
- **Partial negotiation coverage today.** The handlers already return a raw dict for non-HTML callers, but the error path currently only surfaces via the HTML template. The change formalizes a sanitized envelope for both success and error; must ensure the error path no longer leaks raw exception text to JSON callers.
- **Reset idempotency.** Reset stamps "now" each call, so repeated resets move the window start — acceptable and matches existing behavior; the JSON outcome just reports the refreshed state. No new idempotency key needed.
- **Fallback parity.** Keeping `budget.html` as the oracle means two renderers until final retirement; mitigated by tests asserting the JSON shape and the build-aware selection both ways.
