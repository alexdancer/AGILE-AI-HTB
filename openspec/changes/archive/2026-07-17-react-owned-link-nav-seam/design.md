## Context

The React Portal shell has two navigation primitives:

- `AppLink` (`frontend/src/nav.jsx`) — always intercepts a plain left-click and calls `navigate(to)` (History `pushState`), i.e. unconditional client-side navigation.
- Raw `<a href>` — an ordinary full-page navigation.

There is no shared rule for choosing between them, so each view decides per anchor. The correct route-aware primitive already exists but is a private helper in one view:

```js
// frontend/src/views/TaskBreakdownReview.jsx
function isReactOwnedPath(path) { /* second copy of the route list, as regex */ }
function OwnedLink({ to, className, children }) {
  return isReactOwnedPath(to)
    ? <AppLink to={to} className={className}>{children}</AppLink>   // React route → client nav
    : <a href={to} className={className}>{children}</a>;            // otherwise → full page
}
```

`isReactOwnedPath` duplicates the route list that `App.parseRoute` (`frontend/src/App.jsx`) already owns. The two agree today but are independent and will drift the next time a route is added to one and not the other.

Meanwhile the sidebar's `Settings` group links and `+ Open local repo` (`Shell.jsx`) are raw `<a>`, so they full-page-reload routes that React now owns. The `react-portal-shell` spec previously mandated that behavior ("Full-page sidebar links remain full-page navigations"); this change intentionally reverses it for React-owned targets (see the delta spec). Note the code is already ahead of the old spec for `Alarms`, which uses `AppLink` today.

## Goals / Non-Goals

**Goals:**
- One shared, route-aware link seam (`OwnedLink`) in `nav.jsx`, used by every view.
- A single source of truth for "what route does React own": derive `isReactOwnedPath` from `parseRoute`.
- Sidebar `Settings` group and `+ Open local repo` navigate in-shell; Dashboard's internal `/sessions`, `/sessions/{id}`, `/alarms`, `/settings/project` literals navigate in-shell.
- No behavior change for genuinely server-rendered targets (`/login`, `/logout`, bare `/board`, "Server board", error-recovery Retry links).

**Non-Goals:**
- Migrating class-2 server-provided href strings (`action.href`, `links.*_href`, `session_href`, `notice.retryHref`, Setup step `href`s). These come from backend JSON at runtime and are left as-is this pass.
- The `useResource` data-loading consolidation and the Board filter performance work (separate candidates).
- Any backend, FastAPI route, JSON handoff, schema, or auth change.

## Decisions

**1. Extract `parseRoute` into `frontend/src/routes.js`.**
`nav.jsx` needs `parseRoute` to derive route ownership, but `App.jsx` already imports `nav.jsx` (for `NavContext`), so importing `parseRoute` from `App.jsx` into `nav.jsx` would create an import cycle. Move `parseRoute` (a pure, React-free function) into a new `routes.js` imported by both `App.jsx` and `nav.jsx`. Alternative considered: keep `parseRoute` in `App.jsx` and pass an ownership predicate down through context — rejected as more machinery than a plain module for a pure function.

**2. Derive `isReactOwnedPath` from `parseRoute`, not a parallel regex.**
```js
export function isReactOwnedPath(to) {
  return parseRoute(to.split(/[?#]/)[0]).view !== "notFound";
}
```
Stripping `?query`/`#hash` before `parseRoute` handles hrefs like `/settings/workers?adapter_id=…`. This makes the router the sole authority; adding a route to `parseRoute` automatically teaches every `OwnedLink` about it. Alternative considered: keep the regex but add a test asserting it matches `parseRoute` — rejected; deriving is strictly simpler than testing two lists agree.

**3. `OwnedLink` lives in `nav.jsx` beside `AppLink`; `TaskBreakdownReview.jsx` imports both.**
The seam belongs with the other navigation primitives. TBR deletes its two local copies and imports `OwnedLink` / `isReactOwnedPath` from `nav.jsx`; its existing `navigate(...)` guards that call `isReactOwnedPath` switch to the imported version with no behavior change.

**4. Migrate only class-1 static internal literals.**
`Shell.jsx`: `Settings` group (4 links) and `+ Open local repo` (`/projects`) → `OwnedLink`. `Dashboard.jsx`: `/sessions`, `/sessions/{id}`, `/alarms`, `/settings/project` → `OwnedLink`. Leave `/board`, `/login`, `/logout`, "Server board", and Retry links as raw `<a>` (all non-React-owned or deliberately full-page). Dashboard's server-provided `action.href` stays raw `<a>` (class 2, out of scope). Because `OwnedLink` self-decides, migrating a literal that happens to be server-owned is still safe — but this pass keeps the diff to known static React routes.

## Risks / Trade-offs

- **Reversing a ratified nav requirement touches the shell's navigation contract** → captured explicitly as a MODIFIED delta against `react-portal-shell`; the browser-smoke task asserts the new in-shell behavior and the preserved full-page fallbacks.
- **`parseRoute` extraction could break existing imports/tests** → `shell.test.mjs` imports `parseRoute`; update its import to `routes.js` in the same change. `App.jsx` re-exports nothing new; only the definition moves.
- **`OwnedLink` fallback must not client-navigate a server route** → the derived predicate returns `false` for any path `parseRoute` maps to `notFound` (e.g. `/board`), so those stay full-page; add a direct `OwnedLink` test for a known server path.
- **Query-string hrefs** → the `split(/[?#]/)` guard is covered by a test using a `/settings/...?adapter_id=x` input.

## Migration Plan

1. Add `frontend/src/routes.js` with `parseRoute`; update `App.jsx` to import it; update `shell.test.mjs` import.
2. Add `OwnedLink` + derived `isReactOwnedPath` to `nav.jsx`.
3. Delete the local copies from `TaskBreakdownReview.jsx`; import the shared ones.
4. Migrate `Shell.jsx` and `Dashboard.jsx` class-1 anchors to `OwnedLink`.
5. `npm test` + `vite build`; browser-smoke the sidebar Settings/Alarms and Dashboard "view all" links (no full reload) and confirm `/login`/`/logout`/`/board` still full-page.

Rollback is a straightforward revert; no data or backend state is touched.

## Open Questions

- None blocking. Class-2 server-href migration and the `useResource`/Board-filter candidates are deferred by scope, not open questions.
