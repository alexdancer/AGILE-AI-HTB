# UI primitives

Thin React wrappers over the shared class vocabulary in `src/tokens.css`. They
own **no styling of their own** — each renders the same DOM and classes the
views were already hand-writing, so adopting them is a zero-visual-change
refactor. Their value is one source of truth for the props, variants, and
element structure that were previously copy-pasted across 14 views.

Import through the barrel:

```jsx
import {
  Button, Pill, Notice, EmptyState, Loading,
  Panel, PanelHeader, PanelBody,
} from "../components/ui/index.js";
```

## Components

### `Button`

Wraps `.btn`. Polymorphic via `as` so one component covers real buttons,
in-shell `AppLink` navigation, and plain anchors.

```jsx
<Button size="small" type="button" onClick={launch}>Launch</Button>
<Button size="small" variant="secondary" as={AppLink} to={href}>Sessions</Button>
<Button size="small" variant="secondary" as="a" href={sessionHref}>Full Session Report</Button>
<Button size="small" variant="danger" type="button" onClick={block}>Block</Button>
```

- `variant`: `"primary"` (default, bare `.btn`) · `"secondary"` · `"danger"`
- `size`: `"small"` adds `.small`; omit for the default size
- everything else (`type`, `onClick`, `href`, `to`, `disabled`, `aria-*`) passes through

### `Pill`

Wraps `.pill`. `tone` is the semantic modifier; always keep a text label.

```jsx
<Pill tone={launchReady ? "green" : "yellow"}>{launchReady ? "launch ready" : "setup needed"}</Pill>
<Pill tone={queueRunning ? "running" : "idle"}>Queue {status}</Pill>
```

### `Notice`

Wraps `.notice`. `variant` is `"info"` (default) · `"warning"` · `"danger"`.
Pass `role="alert"` for live error notices.

```jsx
<Notice variant="danger">{message}</Notice>
<Notice variant="danger" role="alert">{error}</Notice>
<Notice variant="warning"><strong>Archived project</strong><p className="muted">Restore first.</p></Notice>
```

### `EmptyState` / `Loading`

```jsx
<EmptyState>No completed runs await review.</EmptyState>
<Loading>Loading Pipeline…</Loading>
```

### `Panel` / `PanelHeader` / `PanelBody`

Wraps `.panel` / `.panel-header` / `.panel-body`. `Panel` is polymorphic (`as`,
default `<section>`); `id` and extra classes pass through.

```jsx
<Panel className="planning-inbox">
  <PanelHeader title="Planning Inbox" count={planning.length} />
  <PanelBody className="needs-you-list">{/* … */}</PanelBody>
</Panel>

// Custom trailing marker (nav badge, bare span) → pass `badge`:
<PanelHeader title="Needs You" badge={<span className="nav-badge">{count}</span>} />
<PanelHeader title="Active Worker Runs" badge={<span>{running.length}</span>} />
```

## Migration pattern

Replace the hand-written element with the primitive, keeping the exact same
classes, props, and children. Because the output DOM is identical, existing
render tests stay green. `Board.jsx` is the first migrated view; follow the
same swaps for the rest.
