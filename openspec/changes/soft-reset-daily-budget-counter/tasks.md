## 1. Budget window state

- [x] 1.1 Add `daily_usage_reset_at` preservation to portal token budget settings so saving caps does not discard an existing reset waterline.
- [x] 1.2 Add a shared effective daily budget window helper that returns the later of local-day start and the current-day reset timestamp.
- [x] 1.3 Add database/unit coverage proving reset timestamps are stored without deleting token ledger rows and previous-day reset timestamps do not affect the new day.

## 2. Portal reset action

- [x] 2.1 Add an authenticated Token budget reset POST action that updates only the reset timestamp and redirects back to the Token budget page for browser submissions.
- [x] 2.2 Update the Token budget page to show active budget window start, current-window governed spend, saved daily cap, and clear soft-reset copy.
- [x] 2.3 Add portal tests proving the reset button exists, uses non-destructive wording, and leaves task/session evidence concepts separate from the daily counter.

## 3. Budget consumers

- [x] 3.1 Update dashboard daily governed spend, budget zone, and category summary inputs to use the shared effective budget window.
- [x] 3.2 Update Worker launch preflight remaining-capacity checks and budget override metadata to use the same effective budget window.
- [x] 3.3 Update proxy daily-used and budget alarm calculations to use the same effective budget window.
- [x] 3.4 Add regression tests proving dashboard display, launch guardrails, and alarm/proxy budget comparisons agree after a soft reset.

## 4. Verification

- [x] 4.1 Run targeted token budget, dashboard, proxy, and launch tests affected by the new budget window behavior.
- [x] 4.2 Run `openspec validate soft-reset-daily-budget-counter --strict`.
- [x] 4.3 Run `uv run pytest` and address any failures introduced by this change.
