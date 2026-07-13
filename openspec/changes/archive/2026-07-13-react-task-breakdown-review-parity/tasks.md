## 1. Backend Contract Tests

- [x] 1.1 Add failing route-selection tests for canonical `/task-breakdowns/{id}/review`: complete build serves React, missing/partial build preserves Jinja, auth remains required, direct deep links work, and unknown ids remain backend `404`.
- [x] 1.2 Add failing review-endpoint tests for the normative field matrix: exact top-level/nested JSON types and nullability, proposed/failed/accepted/legacy states, checked-by-default proposed candidates, exact control/link derivation, pageable created Task-id evidence, project/global board targeting, Session links, typed defaults, no-store, and forbidden-field exclusion.
- [x] 1.3 Add failing projection-boundary tests for every text/list bound and selector plus the full case/separator-insensitive redaction policy: credential/PAT/cookie/auth/X-Auth keys, nested headers/env/metadata, bearer/basic, URI credentials, PEM, JWT, every provider-token family, secret paths, mixed safe text, identical preview/continuation source, malformed values, enum normalization, boolean numeric rejection, and forbidden metadata.
- [x] 1.4 Add failing evidence-page tests for every fixed collection id including created Task ids, global constraints, and verification, default/max limits, strict `offset`/`limit` validation, persisted ordinal ordering, generated `next_href`, no-store, unknown-selector `404`, and access beyond every initial page.
- [x] 1.5 Add failing full-text tests for every enumerated fixed/dynamic review text id, complete redacted no-store text, canonical ordinal/field binding, unknown-selector `404`, and no DB/object/filesystem-path interpretation.
- [x] 1.6 Add failing Accept tests for HTML versus explicit JSON negotiation and every exact outcome-table field/type: valid creation/count/board route, presence-aware omitted/present-empty fields, `422`, failed-review `409`, accepted idempotency/count, unknown `404`, internal `500`, fixed safe errors, unchanged editable state on pre-claim validation failure, and fail-closed read-only state on post-claim failure.
- [x] 1.7 Add failing Retry and Manual Candidate tests for HTML versus JSON negotiation and every exact proposed/failed/accepted/validation/unknown/internal outcome-table value, authoritative self refetch, no Task creation, and safe provider/manual validation failures.

## 2. Shared Review State and Bounded Handoffs

- [x] 2.1 Extract a shared Task Breakdown Review context builder from the Jinja GET, including canonical board path, action controls, and legacy candidate normalization without changing Jinja rendering behavior.
- [x] 2.2 Implement reusable complete-string Task Breakdown redaction covering the normative key/value/token/path policy before previewing, plus bounded-text, generated-link, typed-default, fixed-page, and candidate-normalization helpers without serializing raw durable records.
- [x] 2.3 Implement `/api/task-breakdowns/{id}/review` from the normative field matrix with exact review/candidate/context/Repo Context/control/link types, checked-by-default candidate derivation, first bounded pages, created Task-id evidence, and `Cache-Control: no-store`.
- [x] 2.4 Implement no-store allowlisted `/api/task-breakdowns/{id}/review/evidence/{collection_id}` paging for candidates, created Task ids, preserved context, and safe Repo Context collections.
- [x] 2.5 Implement generated `/api/task-breakdowns/{id}/review/text/{text_id}` continuations that recompute only allowlisted review text, redact before returning complete text, use no-store plain text, and reject arbitrary selectors.

## 3. Negotiated Review Actions

- [x] 3.1 Add shared explicit `application/json` negotiation and exact typed/fixed Task Breakdown outcome-table formatting using the existing backend-authoritative mutation paths.
- [x] 3.2 Make Accept map backend domain outcomes to every exact success/idempotent/conflict/validation/not-found/internal transport value while preserving HTML redirects, candidate normalization, Task Estimation, created Task metadata, and board targeting.
- [x] 3.3 Make Retry map backend domain outcomes to every exact proposed/failed/accepted/not-found/internal transport value and authoritative self-refetch target while preserving provider failure records, orchestration evidence, no-Task behavior, and HTML redirects.
- [x] 3.4 Make Manual Candidate map backend domain outcomes to every exact success/accepted/validation/not-found/internal transport value while preserving source fallback, manual HITL policy evidence, no-Task-before-acceptance, and HTML redirects.
- [x] 3.5 Validate all submitted indexes/enums/required text fields and exact Accept/Manual per-field request maxima without reflecting submitted secret values; implement presence-aware omitted-versus-empty parsing so optional/list fields can be cleared; prove pre-claim validation failures preserve editable durable state and untouched fields retain persisted originals.

## 4. Canonical React Route Ownership

- [x] 4.1 Make the canonical Task Breakdown Review GET validate auth/resource existence first, then select React only for a complete build and otherwise execute the shared Jinja fallback.
- [x] 4.2 Extend FastAPI React shell route tests and frontend route parsing for `/task-breakdowns/:breakdownId/review`; prove no parallel `/app/task-breakdowns` route is accepted.
- [x] 4.3 Update React board intake navigation so the existing backend-generated review `next_href` stays in-shell while non-migrated targets retain their current route behavior.

## 5. React Task Breakdown Review

- [x] 5.1 Add frontend tests for loading/error, proposed, failed, accepted, legacy-AFK, project/global, no-candidate, missing-evidence, and paged-overflow render states.
- [x] 5.2 Implement the React review view with source/status/model/session summary; checked-by-default proposed candidate decisions; immediate primary fields; native disclosure for slicing evidence; complete preserved contract, rejected/non-goal/sequence, safe Repo Context, and pageable accepted created Task-id sections.
- [x] 5.3 Implement candidate/context/Repo evidence pagination and generated full-text loading; keep truncated editable fields read-only until full load and disable acceptance until every candidate page is loaded.
- [x] 5.4 Implement browser-local candidate/global edits using existing form field names, submitting only selected and actually edited values; loaded-but-unedited and otherwise untouched persisted values remain backend-authoritative.
- [x] 5.5 Implement Accept, Retry, and Manual Candidate controllers with explicit JSON negotiation, exact outcome handling, success-only navigation/refetch, accepted read-only state, sanitized notices, and local-state preservation on failure.
- [x] 5.6 Implement dirty-state tracking and one confirmation path for in-shell links, Cancel, browser Back/Forward, reload, and close; preserve modified-click behavior and clear guards before successful actions.
- [x] 5.7 Add only scoped shared-token styles needed for dense editable fields, disclosure, paging, failure/accepted states, visible focus, semantic labels, live notices, wrapping, and desktop readability.

## 6. Verification and Review

- [x] 6.1 Run focused Task Breakdown backend tests, React shell/frontend tests, and `npm --prefix frontend run check`; fix all regressions.
- [x] 6.2 Run built/missing/partial route smokes and browser smoke through React board Markdown intake → review → edit/disclosure/full-text/paging → Accept → project board.
- [x] 6.3 Browser-smoke failed review Retry and Manual Candidate recovery, accepted direct load/idempotent routing, unsaved Cancel/Back/reload guards, keyboard operation, visible focus, live announcements, and missing-build Jinja fallback.
- [x] 6.4 Run `uv run pytest -q`, `openspec validate react-task-breakdown-review-parity --strict`, `openspec validate --specs --strict`, and `git diff --check`.
- [x] 6.5 Perform independent review for contract fidelity, complete editable parity, bounded/redacted projections, mutation/idempotency safety, Jinja fallback, draft navigation, accessibility, security/privacy, regression risk, and maintainability; resolve every blocking/significant finding and rerun affected checks.
