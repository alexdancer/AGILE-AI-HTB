## 1. Extract the route table

- [x] 1.1 Create `frontend/src/routes.js` and move `parseRoute` into it verbatim (pure, no React imports)
- [x] 1.2 Update `frontend/src/App.jsx` to import `parseRoute` from `./routes.js` and delete the local definition
- [x] 1.3 Update `frontend/tests/shell.test.mjs` to import `parseRoute` from `../src/routes.js`
- [x] 1.4 `npm test` still green after the move (no behavior change)

## 2. Promote the route-aware link seam into nav.jsx

- [x] 2.1 Add `isReactOwnedPath(to)` to `frontend/src/nav.jsx`, deriving from `parseRoute` (`parseRoute(to.split(/[?#]/)[0]).view !== "notFound"`); export it
- [x] 2.2 Add `OwnedLink({ to, className, children })` to `nav.jsx` (React route → `AppLink`, otherwise → raw `<a>`); export it
- [x] 2.3 In `frontend/src/views/TaskBreakdownReview.jsx`, delete the local `OwnedLink` and `isReactOwnedPath`, import both from `../nav.jsx`, and confirm the two `navigate(...)` guards still call the imported `isReactOwnedPath`

## 3. Migrate class-1 static anchors

- [x] 3.1 `frontend/src/components/Shell.jsx`: convert the `Settings` group links (`/settings/control-plane`, `/settings/budget`, `/settings/project`, `/settings/workers`) and `+ Open local repo` (`/projects`) from raw `<a>` to `OwnedLink`, preserving `className`/active-state logic
- [x] 3.2 Confirm `Shell.jsx` leaves `/login`, `/logout`, and the bare `/board` Planning shim as raw `<a>` full-page anchors
- [x] 3.3 `frontend/src/views/Dashboard.jsx`: convert the `/sessions` and `/alarms` "view all" links, the `/sessions/{id}` session/alarm links, and the `/settings/project` "Connect a project" link to `OwnedLink`
- [x] 3.4 Confirm `Dashboard.jsx` leaves the server-provided `action.href` next-action links and the `/dashboard` error-recovery Retry link as raw `<a>`

## 4. Tests

- [x] 4.1 Add `OwnedLink` unit coverage in `frontend/tests/shell.test.mjs`: a React-owned path renders an in-shell `AppLink`; a non-owned path (`/board`, `/login`) renders a full-page `<a>`; a React path with a `?query` suffix is still owned
- [x] 4.2 Update/extend the sidebar navigation-groups assertions so `Settings` group items and `+ Open local repo` render in-shell links and `/board`/`/login` remain full-page (matches the reversed `react-portal-shell` requirement)

## 5. Verify

- [x] 5.1 `npm test` green and `vite build` succeeds
- [x] 5.2 Browser smoke: clicking a sidebar `Settings` item and Dashboard "view all" navigates in-shell (no full-page reload / nav re-fetch flash); `/login`, `/logout`, and `/board` still perform full-page navigations
- [x] 5.3 `openspec validate react-owned-link-nav-seam --strict`
