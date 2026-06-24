## 1. Data Model and Structured Output

- [x] 1.1 Add `kind` to Task Breakdown candidate validation with allowed values `implementation` and `acceptance_verification`, including backward-compatible handling for existing records without kind.
- [x] 1.2 Add `global_contract_summary` to Task Breakdown Agent result validation and durable Proposed Task Breakdown persistence.
- [x] 1.3 Preserve candidate kind and global contract summary through review form submission and accepted-candidate parsing.

## 2. Task Breakdown Agent Prompt

- [x] 2.1 Update the Task Breakdown Agent system prompt to require one global contract summary for multi-slice breakdowns.
- [x] 2.2 Update the prompt to classify every candidate as `implementation` or `acceptance_verification`.
- [x] 2.3 Update the prompt to auto-propose an `acceptance_verification` candidate recommended last for integrated artifacts, framed as verification rather than whole-task reimplementation.

## 3. Review UX and Accepted Task Metadata

- [x] 3.1 Update the Task Breakdown Review page to display and edit the global contract summary.
- [x] 3.2 Update the review page to display and edit candidate kind with only `implementation` and `acceptance_verification` options.
- [x] 3.3 Ensure accepted implementation Tasks inherit the global contract summary and relevant constraints before Task Estimation.
- [x] 3.4 Ensure accepted Acceptance Verification Tasks include the global contract summary and full original source contract before Task Estimation.
- [x] 3.5 Preserve recommended-last sequence metadata or creation order for Acceptance Verification without adding hard launch-order blocking.

## 4. Tests and Golden Fixtures

- [x] 4.1 Update golden decomposition fixtures to assert candidate kind, global contract summary, and Acceptance Verification for integrated-artifact multi-slice input.
- [x] 4.2 Add regression coverage that implementation slices include the global contract summary without receiving the full source contract.
- [x] 4.3 Add regression coverage that Acceptance Verification receives the full original source contract and is not framed as reimplementation.
- [x] 4.4 Add product-flow coverage for editing global contract summary and candidate kind on the review page.
- [x] 4.5 Add failure/validation coverage for invalid candidate kind values.

## 5. Verification

- [x] 5.1 Run targeted task breakdown, task intake, and portal review tests.
- [x] 5.2 Run `pytest` for the relevant suite before marking this change complete.
