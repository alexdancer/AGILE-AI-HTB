## 1. Dashboard View Model

- [x] 1.1 Update the dashboard route to derive task counts for ready-to-launch and Review tasks from existing task statuses.
- [x] 1.2 Update the dashboard route to derive whether a launchable Worker adapter exists using existing adapter view/readiness data.
- [x] 1.3 Build a small ordered next-actions list with labels, counts, severity, and existing destination URLs.

## 2. Dashboard UI

- [x] 2.1 Add an Operator next actions panel above the existing dashboard KPI cards.
- [x] 2.2 Render Worker setup, launch, review, alarm, and fallback board actions from the next-actions list.
- [x] 2.3 Keep all actions as links to existing pages; do not duplicate launch/review/alarm forms on the dashboard.

## 3. Tests

- [x] 3.1 Add or update portal tests for Worker setup action visibility when no launchable adapter exists.
- [x] 3.2 Add or update portal tests for ready-to-launch and Review task action counts linking to `/board`.
- [x] 3.3 Add or update portal tests for critical/open alarm action counts linking to `/alarms`.
- [x] 3.4 Run targeted portal tests, then run the project test suite if targeted tests pass.
