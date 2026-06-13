# AGILE-AI-HTB Portal — Front-end Mockup

Static, browser-only mockup of the AGILE-AI-HTB governance portal. **No
build, no framework, no live network calls** — open `index.html` in a
browser.

## What's here

| Page          | What it shows                                                |
| ------------- | ------------------------------------------------------------ |
| `index.html`  | Dashboard: budget, active sessions, recent alarms            |
| `sessions.html` | All sessions table + per-session detail (tokens, checkpoints, tool breakdown) |
| `alarms.html` | Alarm inbox with resolve action (mock submit)                |
| `estimate.html` | Task-estimation form + sample estimates                    |
| `proxy.html`  | Animated streaming request trace + governance decision      |

## Data

All values come from `js/fixtures.js` and are obviously synthetic:

- Session / alarm / task IDs: `DEMO_*_2099_*`
- Timestamps: year 2099
- No `prod` / `live` / `staging` strings
- No `fetch()` to real APIs

The data shapes match the real FastAPI responses
(`/session/{id}/report`, `/alarms`, `/alarms/{id}/resolve`, `/estimate`,
`/v1/chat/completions`) so the mockup could later be wired to the live
backend by swapping `fixtures.js` for a thin `fetch()` wrapper.

## How to view

```sh
open docs/mockup/index.html
# or, with a local server:
python -m http.server -d docs/mockup 8000
```

## Tests

`tests/test_mockup_fixtures.py::AGILE_AI_HTBDemoFakeDataInvariantTests`
guards the synthetic-data invariant — it fails the build if any
fixture string looks like a real ID, contains a present-year
timestamp, or references a live API.
