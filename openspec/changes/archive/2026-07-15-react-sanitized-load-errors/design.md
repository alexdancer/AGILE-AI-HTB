## Context

`REACT_PORTAL_PARITY_PLAN.md:331` forbids raw backend detail in operator-facing error UI. Audited across all thirteen React views:

| Pattern | Views |
|---|---|
| `safeError` returning fixed strings by status | Board, Dashboard, Projects, SessionReport, Sessions, Setup, TaskHistory, Workspace |
| `safeError` that passes bounded backend text | Alarms (`:30`) |
| No `safeError`; renders backend text directly | BudgetSettings (`:91`), WorkerSettings (`:200`), ControlPlaneSettings (`:160`), ProjectSettings (`:165`) |

Slice 11a recorded the drift as Decision 6 and deferred it, citing `Alarms.jsx:27` as an example of the established pattern — the one variant that leaks. Three slices later the count is unchanged.

The realistic exposure is modest: `api.js:13` produces `body.detail || JSON.stringify(body)`, and FastAPI's default handler returns `"Internal Server Error"` for a 500 with the traceback going to logs. What an operator actually sees is a `{"detail": …}` blob or a proxy's HTML error page pasted into a notice. That is a correctness and consistency defect, not a breach — and the four offenders are Settings surfaces, the views most likely to echo a base URL, env var name, or adapter path.

## Goals / Non-Goals

**Goals:**

- All thirteen views converge on one load-error pattern.
- The rule stops depending on author discipline.
- The shell's not-found branch stops pointing at a soon-to-be redirect.

**Non-Goals:**

- Changing `api.js`. It is right to carry detail on the Error object; views are wrong to render it. Truncating at the client would hide the defect rather than fix it.
- Action-path `catch` branches (Decision 3).
- Not-found ownership semantics and the `portal-quality-system` fallback scenario — retirement owns both.
- A shared `safeError` module (Decision 2).

## Decisions

### 1. The invariant is the deliverable

Five one-line fixes are not the work; they are the first thing the work catches. This rule has been written down since before slice 1 and violated continuously, because compliance depends on an author copying a compliant neighbour — and 5 of 13 neighbours are wrong, including the one Decision 6 pointed at.

So the change ships a frontend test asserting no view renders backend-derived text in a load-error branch. It costs about what one of the five fixes costs, and it is the only part that survives slice 14. Fixing the five without it buys compliance with no mechanism; the drift has already demonstrated it will return.

The assertion targets `error.message` reaching a view's load-error path — statically, over the view sources. That is coarser than reasoning about rendering, and deliberately so: an unambiguous test that a future author can satisfy by construction beats an exact one nobody can predict.

### 2. Per-view `safeError` locals stay; no shared module

Eight views each carry a small `safeError` with surface-specific copy ("Alarms require sign-in", "Setup state requires sign-in"). 11a's Decision 6 called this deliberate, and it stays.

A shared module would centralise the mechanism but not the copy, so every call site would pass its own strings anyway — the duplication that matters would remain while the file count grew. The invariant test gives the enforcement a shared module would not have provided regardless.

### 3. Load errors and action outcomes are different, and the spec says so

`Projects.jsx:77` renders `boundedError(outcome?.error, …)` from a negotiated action. That backend text is *authored for the operator* — "Local Runner backend is disabled. Run foremanctl init…" — and sanitized server-side by `_safe_worker_evidence`. Suppressing it would replace operator guidance with a fixed string, which is a regression.

A failed handoff is the opposite: nobody wrote that text for an operator. The distinction is the whole rule, so the spec states it normatively rather than leaving the next author to infer it from examples. Action-path `catch` branches (`Board.jsx:35`, `TaskHistory.jsx:56`, `Projects.jsx:62`) sit between the two — a `catch` sees both authored 4xx detail and raw network failure. Keeping them out of scope keeps the invariant unambiguous; they are recorded as follow-up rather than half-fixed here.

### 4. The not-found link is fixed here, not deferred to retirement

`App.jsx:135` links to `/app`. Slice 11b moved every other in-shell target to canonical URLs, and retirement turns `/app` into a redirect, so this branch would silently start costing a redirect hop. It is one line in a file this change already edits, and its spec scenario also pins that the shell must not claim a catch-all — the architecture question `:331` leaves open, answered narrowly enough to be safe.

## Risks / Trade-offs

- **A static assertion can be worked around** → An author who wants to render backend text can still route it through a variable. The test raises the cost of doing it by accident, which is how all five got here; it is not a sandbox.
- **Fixed copy loses diagnostic information** → Intended. The detail belongs in logs and the network tab, not a notice. A 401 is still distinguished because it is actionable ("requires sign-in"); nothing else is.
- **Scope excludes action `catch` branches, so `error.message` still appears in `frontend/src`** → The invariant must therefore target load branches specifically, or it fails on legitimate code. That is the reason for Decision 3's line rather than a wider sweep.

## Migration Plan

No migration. Frontend-only; rollback is reverting the views.

## Open Questions

None.
