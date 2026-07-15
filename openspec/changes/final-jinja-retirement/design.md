## Context

Thirteen Portal surfaces exist twice: once in React, once in Jinja. The Jinja copies are reachable only when the React build is missing or partial, and every canonical route encodes that choice as the same branch:

```python
index = _react_index()
if index is not None:
    return FileResponse(index)
return templates.TemplateResponse(request, "projects.html", {...})
```

Roughly fifteen sites repeat it (`portal.py` ×13, `alarms.py:85`, `tasks.py:483`). The templates are frozen by plan rule — kept executable as fallback and as a parity oracle — and both jobs are now done. Slices 1–11b proved parity surface by surface and moved each onto its canonical URL; slice 10 severed `login.html` from `base.html` so a recovery surface would survive this change.

The constraint that shapes everything below: **deleting the templates deletes the fallback, so the fallback's contract must be replaced in the same diff, not merely removed.** Seven durable specs currently promise Jinja-when-unbuilt. Those promises are true today. A change that deletes the templates without rewriting them leaves the specs describing a system that does not exist.

`login.html` is the sole survivor, and `portal-local-access:57-63` already pins what that means: "Login survives retirement of the duplicated surfaces … it SHALL depend on no removed template, layout, or shared style block." That scenario is this change's acceptance test, pre-written.

## Goals / Non-Goals

**Goals:**

- Delete the 16 duplicated templates and every route branch that reaches them.
- Give missing-build one answer, at every React-owned route, with copy that is true.
- Convert `/app/*` from transitional alias to permanent redirect.
- Rewrite the seven specs' fallback promises in the same diff as the deletion.
- Make re-introduction of a retired template a failing test.

**Non-Goals:**

- Changing authentication strength, workflow rules, guardrails, or budget semantics.
- Changing the React views, their JSON handoff contracts, or the shared action endpoints. Those endpoints are shared, not duplicated; React calls them with `Accept: application/json` and non-JSON callers keep their redirects.
- Visual redesign. The plan defers branding and design-system work to after retirement.
- Removing the `/board` shim, which redirects to the first connected project's board and has no React view by explicit spec.

## Decisions

### 1. Missing build returns the recovery response everywhere; the landing stops checking

Today the landing is build-aware. `_default_portal_landing` (`portal.py:1955`) probes `react_shell_available()` and diverts to a Jinja first-project or `/projects` page when the build is incomplete, and `react-portal-shell:327` promises the operator "SHALL NOT receive a blank shell or missing-build `503` as the default landing."

Retirement deletes the divert target. Two replacements were considered:

| Option | Behavior | Cost |
|---|---|---|
| Landing stays build-aware | `/` renders recovery inline at `200` | Keeps the build-check branch on the landing path; two routes render recovery; the operator gets a `200` for a Portal that cannot work |
| **Landing stops checking** (chosen) | `/` → `302 /dashboard` → `503` recovery | The default landing can now be a `503` — a direct inversion of the current promise |

Chosen the second. `_default_portal_landing` collapses to `return "/dashboard"`, which means the function and its `database_path` argument disappear rather than being rewritten — the branch is not replaced with a different branch, it is deleted. One surface renders recovery, one status code means "not built", and every React-owned route behaves identically whether the operator typed it, bookmarked it, or was redirected to it.

The inverted promise is honest: after retirement a missing build *is* a broken Portal, and a `503` naming the build command is more actionable than a `200` on a page that cannot do anything. `/login` remains `200` server-rendered throughout, which is what preserves operator access.

### 2. The recovery page loses its link rather than gaining a new one

`_MISSING_BUILD_HTML` (`react_shell.py:48-64`) currently reads:

> Build the frontend with `cd frontend && npm install && npm run build`, **or use the server-rendered pages instead.**
> [Open the server-rendered Portal](/projects)

After retirement both halves are wrong: there are no server-rendered pages, and `/projects` returns this very document. The link points at the error it is apologizing for.

Considered pointing it at `/login` instead. Rejected — logging in leads to `/dashboard`, which is this page again. There is no in-Portal destination that helps, because the Portal is what is missing. The honest recovery page states the build command and offers no link. Its independence is the same property slice 10 established for `login.html`: a recovery surface cannot share machinery with the thing that might be broken.

### 3. Inverted requirements are removed and replaced, not edited in place

Two requirement titles contradict the post-retirement state outright:

- `react-portal-shell`: "React is the build-aware default authenticated landing"
- `portal-quality-system`: "Portal remains server-rendered"

A `MODIFIED` block would leave a requirement whose heading asserts the opposite of its body. Both are instead `REMOVED` with Reason and Migration, plus an `ADDED` replacement — "React is the default authenticated landing" and a recovery-surface requirement respectively. The remaining five specs take ordinary `MODIFIED` blocks, since only their fallback clauses change and their titles stay accurate.

### 4. `portal-quality-system` changes in this diff, not before it

Its scenarios "No frontend framework is required for Jinja fallback and non-migrated pages" (`:38-40`) and "Non-migrated pages require no frontend build step" (`:30-33`) enumerate pages this change deletes. Both are **true at HEAD** — the Portal really does render without a Node build today. Editing them ahead of the deletion would make the spec lie about the current tree; editing them after would leave a window where it lies about the new one. Same commit, both directions.

### 5. `/app/*` redirects permanently with `301`

The three alias routes are GET-only, so method preservation (`307`/`308`) buys nothing, and `301` states the intent that the alias is over. Nothing internal targets `/app`: `_workspace_action_href` (`react_shell.py:793-805`) already maps an inbound `/app/projects/{id}/board` onto the canonical board href, and slice 11b removed the last link. The redirects exist for operator bookmarks and external links only.

The redirect must sit *before* the auth dependency's effect is observable to an unauthenticated caller in the sense that matters here: it is a pure URL translation, so it may redirect without authenticating. Deep-linking `/app/projects/{id}` while logged out should land on `/login` via the canonical route's own guard, not leak project existence through a redirect that 404s differently. Simplest correct form: keep `require_portal_auth` on the redirect routes exactly as the shell routes have it today, so the auth boundary is unchanged by this change.

### 6. The invariant test asserts the directory, not just the routes

Plan `:333` requires "an invariant test preventing normal routes from rendering retired templates." Route-level assertions alone would pass if someone re-added `dashboard.html` but wired it to a new URL. The invariant is therefore two-part:

1. The templates directory contains exactly `login.html` — a set equality, so adding any template fails without needing a route to exercise it.
2. With the build absent, every React-owned canonical route returns the recovery `503`; `/login` still returns `200`.

Part 2 reuses the rehearsal from slice 10 (`880b3ad`), which already proved `/login` renders with `base.html` moved aside. That was verified once by hand; this pins it permanently.

### 7. Oracle *scenarios* change; oracle *prose* stays

Several specs name Jinja not as a page that must exist, but as the baseline React was measured against. The line drawn here: **a scenario whose `WHEN` requires rendering a deleted page must change, because it becomes impossible to execute. Requirement prose that describes where a contract came from may stay, because it is a historical claim that remains true.**

Changed under this rule — both are scenarios that execute the deleted page:

- `react-portal-shell` "Dashboard JSON agrees with Jinja dashboard state" (`:83`) — its `WHEN` requests "the React dashboard JSON **and Jinja `/dashboard`** for the same database state". Replaced with a scenario asserting derivation from the shared context builder, which is what the comparison was really protecting and is still executable.
- `react-portal-shell` "Projects JSON agrees with the server-rendered projects page" (`:526`) — same shape, same replacement.

Left alone under this rule — all are prose, none are executed by a scenario:

- `portal-evidence-readability:126` "parity with the current Jinja report" and `:160` "no … evidence visible in Jinja SHALL become inaccessible when React is built".
- `task-breakdown-review:49` "React SHALL preserve all source-contract and classification evidence visible in the Jinja review".
- `react-portal-shell:639,788,965,1110` — "matching Jinja's checked-by-default behavior", "preserves every field the Jinja history page shows", "the same computation the Jinja page uses", and similar. The *computations* these name survive retirement; only the page reading them goes.

The parity these clauses assert was discharged when each React view shipped, and the archived changes record the oracle. Rewriting them would widen this change without altering behavior. Accepted as debt; revisit if the wording ever blocks a change.

### 8. Action-path redirect wording is out of scope

Six requirements say the action endpoints preserve "the current Jinja redirect for HTML callers" (`react-portal-shell:227`, `:806`, `:846`, `:908`, `:984`, `:1058`), and `:242` says the alarm resolve redirect goes "back to the Jinja alarms page". Retirement does not falsify these. The endpoints still `302` to `/alarms`, `/settings/budget`, and the rest; those URLs still resolve; only the renderer behind them changed — and it changed when each slice shipped, not here. The wording is pre-existing drift naming a renderer where the URL is what is normative. Out of scope, for the same reason as Decision 7.

The one place this genuinely bites is `react-board-workflow`, where the scenario "Existing Jinja form behavior remains available" has a `WHEN` premise — "a **Jinja board form** submits" — that becomes unreachable once `board.html` is deleted. That is a scenario executing a deleted page, so Decision 7 puts it in scope: it becomes "Non-JSON callers keep the existing redirect behavior", which preserves the guarantee for `curl` and any other non-JSON client.

### 9. The test suite's oracle is Jinja; it moves to the JSON handoffs

This is the largest piece of work in the change, and it was invisible until implementation started.

`tests/conftest.py:9-16` pins **every** test to "build absent" through an autouse fixture — built-shell tests opt in by monkeypatching `react_build_dir`. So the 858-test suite reaches Portal routes through the Jinja fallback by default, and 141 assertions across 19 files in four test packages (`tests/portal`, `tests/api`, `tests/workers`, `tests/config`, `tests/evals`) read rendered Jinja markup as their oracle for backend state:

```python
# tests/workers/test_adapter_verification.py:1035 — a Worker test, not a Portal one
response = client.get("/settings/workers?adapter_id=opencode", ...)
assert 'action="/settings/workers/opencode/verify"' in response.text
assert "CLI: Track native usage after run" in response.text
```

Retirement does not remove the behavior these assert. It removes the surface they read it through. Three options:

| Option | Cost |
|---|---|
| Assert the recovery `503` instead | Converts 141 assertions about backend behavior into 141 assertions that a `503` is a `503`. Silently deletes the coverage while leaving the suite green — the worst outcome, and what an earlier draft of this change's task list wrongly prescribed |
| Flip the fixture to build-present; move UI assertions to `frontend/tests` | Matches how the product runs, but splits Portal coverage across two suites and needs a fake-build fixture satisfying `_referenced_assets_available` |
| **Migrate each assertion to the JSON handoff** (chosen) | Largest mechanical effort; preserves what the suite actually proves |

Chosen the third. The translation target already exists and is already normative: `react_shell.py` serves `/api/dashboard`, `/api/settings/workers`, `/api/settings/control-plane`, `/api/settings/budget`, `/api/settings/project`, `/api/setup`, `/api/projects`, `/api/alarms`, and the per-project endpoints, each with a bounded field contract this specification pins. A test asserting `"CLI: Track native usage after run"` in HTML is really asserting `tracking.mode == "native_usage"`, and the handoff says so more precisely than the markup did.

A minority of the 141 are pure presentation — `"Only used by API / Proxy mode"` — with no JSON equivalent, because they assert React's copy rather than the backend's state. Those move to `frontend/tests` where the React view owns them, or are dropped when the React view's existing tests already cover them. Dropping requires a recorded reason in the task, never a silent deletion.

## Risks / Trade-offs

- **A missing build now yields `503` at the default landing, where an operator previously got a working page** → This is the change, not an accident. Mitigated by the recovery page naming the exact build command, by `/login` staying server-rendered, and by `npm run build` being an existing documented gate. The population at risk is operators running from source without building — the same people the recovery copy addresses.
- **A spec is missed and keeps promising Jinja** → Seven were found by grepping `Jinja` across `openspec/specs/` (77 hits in `react-portal-shell`, 15 across six others) and classifying each as normative or retrospective. Verification reruns that grep and requires every survivor to be retrospective or about login.
- **Deleting shared context builders breaks a React handoff** → Several `_*_context` helpers feed both a Jinja branch and a React JSON endpoint by explicit design (`react_shell.py` reuses `_dashboard_context`, `_effective_budget_settings`, `_setup_overview_state`, `board_page_context`). Delete only what the deleted branch alone called; the 858-test suite plus the React check are the gate.
- **`login.html` at `880b3ad` is a reconstruction** → Provenance is an open item from the prior session (rebuilt after a `git checkout` clobbered the uncommitted original, verified behaviorally). Retirement makes it the only template, which raises the cost of an undetected discrepancy. Diff it against any surviving original before deleting its siblings, while `base.html` still exists to compare against.
- **`tasks.py` / `alarms.py` keep dead `Jinja2Templates` instances** → Removing them is in scope; if a hidden consumer appears, leaving the instance is harmless and the invariant test still passes. Prefer removal, accept retention.

## Migration Plan

No data migration, no schema change, no config change. The order that keeps the tree green:

1. Diff `login.html` against any surviving original — this is the last moment `base.html` exists to compare against.
2. Add the invariant test and the recovery assertions first, expected to fail. They define done.
3. Replace the fallback branches with the recovery response, route by route, leaving templates in place. Suite stays green except the new tests.
4. Delete the 16 templates and the now-unreachable context builders, `_default_portal_landing`, and the dead `Jinja2Templates` instances.
5. Convert `/app/*` to `301`.
6. Rewrite the seven specs and correct the stale docstrings and plan ledger — same commit as step 4 per Decision 4.

Rollback is `git revert`: the change removes files and branches, adds no state, and touches no operator data. An operator on a reverted build gets the Jinja fallback back unchanged.

## Open Questions

None blocking. The missing-build behavior was decided explicitly (Decision 1); the provenance diff (step 1) is cheap insurance rather than a blocker, and the plan's revisit condition for React login — multi-user, SSO, or password reset — remains recorded in the Decision Log and unaffected by this change.
