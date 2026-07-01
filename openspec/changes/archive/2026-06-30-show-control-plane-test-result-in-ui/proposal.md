## Why

The Control Plane connection test currently sends browser form submissions to a raw JSON response page. Operators need the test result to stay in the settings UI, with clean success/failure feedback and sanitized evidence.

## What Changes

- Keep `/settings/control-plane/test` as the same authenticated test action.
- Return browser/form submissions to `/settings/control-plane` after recording the test result instead of leaving the operator on JSON.
- Render the last test result as a concise UI status with sanitized provider/model/usage/error fields.
- Keep raw/sanitized evidence auditable behind a native disclosure.
- Preserve JSON responses for API clients.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `control-plane-model-connection`: connection tests must present browser results in the Control Plane settings UI while preserving sanitized JSON behavior for API clients.

## Impact

- Portal Control Plane settings route and template.
- Portal tests for browser-style connection test submission and JSON API behavior.
- No database schema change.
- No new dependency.
- No Worker Adapter model/auth changes.
