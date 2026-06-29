## 1. Tests First

- [x] 1.1 Add portal dashboard coverage where only Agent Review/reporting tokens exist and the daily budget card/zone uses those tokens instead of showing Worker execution `0` as the budget used value.
- [x] 1.2 Update budgeted launch coverage so prior control-plane/reporting/Agent Review token rows reduce daily remaining budget and can block Worker launch when the daily cap is exhausted.
- [x] 1.3 Preserve regression coverage that Agent Review/reporting tokens do not update task `actual_tokens` or Worker execution session totals.
- [x] 1.4 Add or update token budget settings copy assertions so the page describes daily governed model-spend budget plus per-session Worker execution cap.

## 2. Budget Accounting Semantics

- [x] 2.1 Add a small budget-usage helper or equivalent route/service logic that returns current-period total governed token spend from the token ledger, including `worker_execution`, `control_plane`, `task_breakdown`, `adapter_verification`, `reporting_summary`, and `other` rows.
- [x] 2.2 Update dashboard daily budget and current zone calculation to use total governed token spend instead of `by_category.worker_execution`.
- [x] 2.3 Update Worker launch daily budget checks to subtract total governed current-period spend before evaluating a task's estimated Worker execution tokens.
- [x] 2.4 Keep per-session Worker execution cap checks and task `actual_tokens` based on Worker execution evidence only.
- [x] 2.5 Update proxy/budget alarm calculations that currently read current-day Worker-only usage so daily alarms reflect total governed spend while session usage remains Worker execution scoped.

## 3. Portal Copy and Breakdown

- [x] 3.1 Rename dashboard copy from “Daily budget (Worker execution)” to daily governed model-spend budget language.
- [x] 3.2 Render a visible category breakdown that includes Worker execution, review/reporting, planning/breakdown, setup/verification, and other tracked tokens.
- [x] 3.3 Remove or replace misleading `control-plane/setup spend is separate` copy on dashboard and budget setup pages.
- [x] 3.4 Keep Worker execution totals visible as Worker-only evidence so operators can still distinguish coding harness spend from orchestration spend.

## 4. Verification

- [x] 4.1 Run targeted tests for budgeted launch, dashboard, task review, and session/report token accounting.
- [x] 4.2 Run `openspec validate count-orchestration-tokens-in-budget --strict`.
- [x] 4.3 Run `uv run pytest` after implementation and update tasks only after the relevant checks pass.
