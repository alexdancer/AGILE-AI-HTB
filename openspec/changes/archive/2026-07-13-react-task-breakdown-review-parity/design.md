## Context

The canonical `/task-breakdowns/{breakdown_id}/review` GET and the Accept, Retry, and Manual Candidate POSTs live in `routes/tasks.py`. The GET currently passes a raw durable breakdown record to `task_breakdown_review.html`; the POST handlers read the same record, normalize operator form edits, invoke existing Task Estimation, persist accepted candidates and created Task ids, and redirect to either the project board or review. React board intake already receives the canonical review URL as `next_href`, but follows it with a full-page navigation because React does not own that route.

This slice migrates that canonical workflow without changing Task Breakdown Agent output, Task Estimation, Task creation semantics, or persistence. FastAPI remains authoritative. Jinja remains the missing/partial-build fallback and parity oracle.

## Goals / Non-Goals

**Goals:**

- Own the canonical Task Breakdown Review route in React when the complete frontend build is available.
- Preserve every currently visible/editable review field, failed-review recovery path, accepted-review evidence, Session Report link, and project-scoped board return.
- Expose exact authenticated browser contracts without serializing raw records or irreversibly hiding bounded content.
- Keep drafts local to the loaded React page and protect unsaved edits from accidental navigation.
- Reuse existing Accept, Retry, and Manual Candidate handlers with explicit JSON negotiation and unchanged HTML behavior.

**Non-Goals:**

- No database migration beyond the defaulted monotonic Task Breakdown `revision`, server-side draft/autosave, collaborative editing, new Task Breakdown Agent fields, estimator/routing change, or atomic-batch redesign of acceptance.
- No generic form/state framework, generalized JSON mutation API, websocket/polling contract, mobile redesign, or visual rebrand.
- No Jinja deletion, Task History migration, Alarm migration, Settings migration, or `/app/task-breakdowns` alias.

## Decisions

### 1. Shared backend state precedes both renderers

Extract a private Task Breakdown Review context builder that loads the durable record, computes the canonical board path, normalizes legacy candidate execution mode exactly as the existing Jinja/acceptance path does, and derives action availability. The Jinja GET consumes this shared state unchanged. The React projection allowlists from the same state.

Alternative: project directly from the raw DB row or duplicate legacy/default rules in React. Rejected because it would create split authority and expose persisted metadata shapes.

### 2. Canonical GET is build-aware and validates identity before shell serving

`/task-breakdowns/{breakdown_id}/review` checks auth and review existence before selecting a renderer. A complete frontend build serves the React index; missing/partial build executes the existing Jinja renderer at the same URL. Unknown ids remain backend `404`s even when the build exists. No parallel `/app/task-breakdowns/...` route is introduced.

Alternative: keep the canonical Jinja route and add an `/app` alias. Rejected because the migration plan requires one canonical route tree.

### 3. Review JSON is exact, bounded, pageable, and redacted before truncation

`GET /api/task-breakdowns/{breakdown_id}/review` returns exactly `review`, `candidates`, `context`, `repo_context`, `controls`, and `links`.

- `review`: exactly `id`, `status`, `decision`, `model`, `session_id`, `session_href`, `rationale`, `source_text`, `failure_type`, `failure_message`, and `created_task_ids`.
- `candidates`: a page object with exactly `items` and `pagination`; pagination has exactly `offset`, `limit`, `total`, `has_more`, and generated `next_href`.
- Each candidate: exactly `index`, `accepted_by_default`, `kind`, `execution_mode`, `title`, `objective`, `prompt`, `acceptance_criteria`, `proof`, `hitl_reason`, `constraints`, `why_this_task_exists`, `why_not_smaller`, `why_not_larger`, `dependencies`, and `likely_entry_points`.
- `context`: exactly `global_contract_summary`, `global_constraints`, `verification`, `rejected_items`, `non_goals`, and `recommended_sequence`. List-valued evidence uses page objects.
- Each rejected item: exactly `text` and `reason`.
- `repo_context`: exactly `available`, `source`, `text_chars`, `documents`, `manifests`, `entrypoints`, `test_commands`, and `tracked_files_sample`; project root is excluded. Each list is a page object.
- `controls`: exactly `can_accept`, `can_retry`, and `can_create_manual_candidate`.
- `links`: exactly `self_href`, `api_href`, `board_href`, `accept_href`, `retry_href`, and `manual_href`.

The following matrix is normative. “Bounded text” means an object with exactly string `preview`, boolean `truncated`, and nullable generated string `full_href`. “Page” means exactly `items` plus `pagination`; pagination is exactly non-negative integer `offset`, positive integer `limit`, non-negative integer `total`, boolean `has_more`, and nullable generated string `next_href`. Booleans are never accepted as integers.

| Path | JSON type and nullability | Malformed/default or derivation | Bound and continuation |
| --- | --- | --- | --- |
| `review.id` | string | current route-bound durable id; unsafe/unknown ids produce route `404` | canonical `[A-Za-z0-9_-]{1,128}`; never truncated |
| `review.status` | enum string | `proposed`, `failed`, or `accepted`; malformed becomes `failed` | never truncated |
| `review.decision` | enum string | `single_task`, `proposed_task_breakdown`, or `manual_required`; malformed becomes `manual_required` | never truncated |
| `review.model` | bounded text | wrong type becomes empty text | 200; selector `model` |
| `review.session_id` | string or `null` | only a canonical safe id is retained; wrong/unsafe/missing becomes `null` | `[A-Za-z0-9_-]{1,128}`; never truncated |
| `review.session_href` | string or `null` | generated from retained `session_id`; otherwise `null` | route-generated; never persisted input |
| `review.rationale` | bounded text | wrong type becomes empty text | 4,000; selector `rationale` |
| `review.source_text` | bounded text | wrong type becomes empty text | 20,000; selector `source` |
| `review.failure_type` | bounded text or `null` | wrong/missing becomes `null` | 200; selector `failure-type` |
| `review.failure_message` | bounded text or `null` | wrong/missing becomes `null` | 4,000; selector `failure-message` |
| `review.created_task_ids` | page of bounded-text ids | wrong type becomes empty page; each non-string item becomes empty text | 50 default/100 max; item preview 128; selector `created-task-{ordinal}` |
| `candidates` | page of candidate objects | wrong type becomes empty page | 20 default/50 max; evidence id `candidates` |
| candidate `index` | non-negative integer | persisted zero-based ordinal, never record input | never truncated |
| candidate `accepted_by_default` | boolean | `true` for every candidate while status is `proposed`; otherwise `false` because accepted reviews are read-only | never read from persisted candidate data |
| candidate `kind` | enum string | invalid/missing becomes `implementation` | `implementation` or `acceptance_verification`; never truncated |
| candidate `execution_mode` | enum string | existing normalization: `AFK` only for valid `AFK` or legacy `human_in_loop: false`; otherwise `HITL` | never truncated |
| candidate `title` | bounded text | wrong type becomes empty text | 500; candidate selector field `title` |
| candidate `objective` | bounded text | wrong type becomes empty text | 8,000; field `objective` |
| candidate `prompt` | bounded text | wrong type becomes empty text | 20,000; field `prompt` |
| candidate `acceptance_criteria` | bounded text | wrong type becomes empty text | 8,000; field `acceptance-criteria` |
| candidate `proof` | bounded text | wrong type becomes empty text | 8,000; field `proof` |
| candidate `hitl_reason` | bounded text | wrong/missing becomes empty text | 4,000; field `hitl-reason` |
| candidate `constraints` | bounded text of newline-joined string items | wrong outer type becomes empty; non-string items are omitted | 8,000; field `constraints` |
| candidate `why_this_task_exists` | bounded text | wrong type becomes empty text | 4,000; field `why-this-task-exists` |
| candidate `why_not_smaller` | bounded text | wrong type becomes empty text | 4,000; field `why-not-smaller` |
| candidate `why_not_larger` | bounded text | wrong type becomes empty text | 4,000; field `why-not-larger` |
| candidate `dependencies` | bounded text of newline-joined string items | wrong outer type becomes empty; non-string items are omitted | 8,000; field `dependencies` |
| candidate `likely_entry_points` | bounded text of newline-joined string items | wrong outer type becomes empty; non-string items are omitted | 8,000; field `likely-entry-points` |
| `context.global_contract_summary` | bounded text | wrong type becomes empty text | 20,000; selector `global-contract` |
| `context.global_constraints` | page of bounded text | wrong type becomes empty page; non-string items become empty text | 50/100; evidence id `global-constraints`; selector `global-constraint-{ordinal}` |
| `context.verification` | page of bounded text | wrong type becomes empty page; non-string items become empty text | 50/100; evidence id `verification`; selector `verification-{ordinal}` |
| `context.rejected_items` | page of objects exactly `text`, `reason`, each bounded text | wrong outer type becomes empty page; wrong item becomes empty text/reason | 50/100; evidence id `rejected-items`; selectors `rejected-{ordinal}-text`/`reason` |
| `context.non_goals` | page of bounded text | wrong type becomes empty page; non-string items become empty bounded text | 50/100; evidence id `non-goals`; selector `non-goal-{ordinal}` |
| `context.recommended_sequence` | page of bounded text | wrong type becomes empty page; non-string items become empty bounded text | 50/100; evidence id `recommended-sequence`; selector `recommended-sequence-{ordinal}` |
| `repo_context.available` | boolean | `true` only when the allowlisted Repo Context object contains usable source or collection evidence; otherwise `false` | derived, never persisted boolean authority |
| `repo_context.source` | bounded text or `null` | wrong/missing becomes `null` | 2,000; selector `repo-source` |
| `repo_context.text_chars` | non-negative integer | wrong/negative/boolean becomes zero | never truncated |
| Repo Context collections | page of bounded text | wrong outer type becomes empty page; non-string items become empty text | 50/100; allowlisted collection ids/selectors below |
| `controls.can_accept` | boolean | `true` exactly when normalized status is `proposed` and at least one candidate exists | derived |
| `controls.can_retry` | boolean | `true` exactly when normalized status is `failed` | derived |
| `controls.can_create_manual_candidate` | boolean | `true` exactly when normalized status is `failed` | derived |
| `links.self_href`, `api_href`, `board_href` | string | generated from current review id and canonical board helper | never persisted input |
| `links.accept_href` | string or `null` | generated only when `can_accept`; otherwise `null` | never persisted input |
| `links.retry_href`, `manual_href` | string or `null` | generated only when the matching control is true; otherwise `null` | never persisted input |

Follow-up pages use `/api/task-breakdowns/{id}/review/evidence/{collection_id}` with exact fixed ids `candidates`, `created-task-ids`, `global-constraints`, `verification`, `rejected-items`, `non-goals`, `recommended-sequence`, `repo-documents`, `repo-manifests`, `repo-entrypoints`, `repo-test-commands`, and `repo-tracked-files`. Candidate pages default to 20 and reject limits above 50. Every other evidence page defaults to 50 and rejects limits above 100. Query values are strict non-negative `offset` and positive bounded `limit`; malformed, negative, zero, or over-limit values return `422`. Every page preserves persisted ordinal. Unknown selectors return `404` and are never interpreted as DB fields, object paths, or filesystem paths.

Fixed text ids are exactly `model`, `rationale`, `source`, `failure-type`, `failure-message`, `global-contract`, and `repo-source`. Candidate ids are exactly `candidate-{ordinal}-{field}` where canonical non-negative decimal `ordinal` binds to the persisted candidate ordinal and `field` is one of `title`, `objective`, `prompt`, `acceptance-criteria`, `proof`, `hitl-reason`, `constraints`, `why-this-task-exists`, `why-not-smaller`, `why-not-larger`, `dependencies`, or `likely-entry-points`. Preserved-context ids are exactly `global-constraint-{ordinal}`, `verification-{ordinal}`, `rejected-{ordinal}-text`, `rejected-{ordinal}-reason`, `non-goal-{ordinal}`, and `recommended-sequence-{ordinal}`. Created Task ids use exactly `created-task-{ordinal}`. Repo Context ids are exactly `repo-document-{ordinal}`, `repo-manifest-{ordinal}`, `repo-entrypoint-{ordinal}`, `repo-test-command-{ordinal}`, and `repo-tracked-file-{ordinal}`.

All main review JSON, evidence-page JSON, and full-text responses use `Cache-Control: no-store`. Full text uses `text/plain; charset=utf-8`. Redaction returns a complete string and never truncates; the same complete redacted value feeds both preview and continuation.

The redactor normalizes key names case-insensitively across dash/underscore/space separators. It removes values for keys/header/environment names containing or equaling `api-key`, `apikey`, `token`, `secret`, `password`, `passwd`, `credential`, `authorization`, `proxy-authorization`, `cookie`, `set-cookie`, `x-auth`, `access-token`, `refresh-token`, `id-token`, `github-pat`, `personal-access-token`, `private-key`, `client-secret`, or `session-token`, plus the exact key `pat` and environment-style names ending `_TOKEN`, `_KEY`, `_SECRET`, `_PASSWORD`, `_CREDENTIAL`, or `_COOKIE`. It redacts assignment/header values for those names inside free text and JSON-like text, including nested `headers`, `environment`, `env`, and `metadata`. It replaces bearer/basic authorization values, URI user-info passwords, PEM private-key blocks, JWT-like three-segment values, and provider token families `sk-`/`sk_`, `ghp_`, `github_pat_`, `gho_`, `ghu_`, `ghs_`, `glpat-`, `xoxb-`, `xoxp-`, `xoxa-`, `xoxr-`, and AWS access-key ids with `[REDACTED]` while preserving surrounding safe text. Repo Context path/list entries whose path segments are `.env` or any `.env.*` variant, `.npmrc`, `.pypirc`, `credentials` or any `credentials.*` variant, `secrets` or any `secrets.*` variant, `id_rsa`, or `id_ed25519` are omitted. There is no generic-token exception on this surface because token-count evidence is not projected here.

Contract tests include mixed safe-plus-secret strings and case/separator variants for credentials, PATs, cookies, `Set-Cookie`, `Authorization`, proxy authorization, `X-Auth-*`, nested headers/environment/metadata, bearer/basic values, URI credentials, PEM keys, JWTs, every named provider token family, and secret-named path entries. They prove that preview and full continuation are derived from the identical complete redacted value and that safe surrounding text remains available.

### 4. Bounded editable values use load-before-edit and omission for untouched fields

React displays each bounded preview. If an editable value is truncated, the field is read-only until its generated full-text action successfully loads the complete redacted value. Loading alone does not dirty or submit the field. The accept request omits every untouched field, including loaded-but-unedited fields, so the presence-aware backend parser preserves its authoritative persisted value. Only an actual operator edit submits the field's complete current redacted value. Candidate acceptance remains indexed against the backend candidate ordinal, and the UI must load all candidate pages before enabling final acceptance so unseen candidates cannot be silently accepted or discarded.

Form parsing becomes presence-aware for parity fields for both HTML and JSON-negotiated callers: an omitted field preserves the persisted original; a present empty optional string or newline-list clears that value; and a present empty required global contract, title, prompt, objective, proof, slicing-rationale, or HITL-reason field follows candidate validation and returns `422` when invalid for the selected candidate. This applies to candidate constraints/dependencies/entry points and global constraints/verification as well as scalar fields. HTML keeps its existing form representation and `303` destinations, while both transports use the same backend domain parser.

Alternative: submit truncated previews or silently cap candidate count. Rejected because either corrupts accepted tasks or hides work.

### 5. Existing POSTs gain one negotiated outcome envelope

React sends `Accept: application/json` with the existing form field names. HTML/form callers keep current `303` targets and error behavior. JSON responses contain exactly `ok`, `error`, `next_href`, `retry_href`, `breakdown_id`, `status`, and `created_task_count`. `ok` is boolean; `error`, `next_href`, `retry_href`, `breakdown_id`, and `status` are string or `null`; `created_task_count` is a non-negative integer that rejects booleans. Hrefs are generated only from the known review and canonical board helpers.

Edited Accept values use hard request maxima distinct from display previews: title 1,000 characters; objective, HITL reason, and each why field 20,000; prompt 100,000; acceptance criteria and proof 40,000; each newline-joined candidate constraints/dependencies/entry-points field 40,000; global contract 50,000; global constraints and verification 50,000 each. Manual Candidate uses title 1,000, prompt 100,000, and acceptance criteria 40,000. Omitted untouched fields retain persisted originals regardless of their current size; present empty optional/list values clear those values. Unknown, malformed, or out-of-range candidate indexes return the fixed `422` outcome; selected canonical indexes undergo kind/execution/required-text validation.

The following outcome table is normative (`self` means `/task-breakdowns/{id}/review`; `board` means the existing canonical project/global board helper):

| Action/outcome | HTTP | `ok` | `error` | `next_href` | `retry_href` | `breakdown_id` | `status` | `created_task_count` |
| --- | ---: | --- | --- | --- | --- | --- | --- | ---: |
| Accept proposed success | 200 | `true` | `null` | board | `null` | current id | `accepted` | full durable created-id count |
| Any action, already accepted | 200 | `true` | `null` | board | `null` | current id | `accepted` | full durable created-id count |
| Accept failed review | 409 | `false` | `Review must be retried or replaced manually before acceptance.` | `null` | self | current id | `failed` | 0 |
| Accept validation/no selection | 422 | `false` | `Task breakdown acceptance is invalid.` | `null` | self | current id | normalized current status | 0 |
| Retry completed with proposed result | 200 | `true` | `null` | self | `null` | current id | `proposed` | 0 |
| Retry completed with persisted failed result | 200 | `true` | `null` | self | `null` | current id | `failed` | 0 |
| Manual Candidate success | 200 | `true` | `null` | self | `null` | current id | `proposed` | 0 |
| Manual Candidate validation failure | 422 | `false` | `Manual candidate is invalid.` | `null` | self | current id | normalized current status | 0 |
| Any action, unknown review | 404 | `false` | `Task breakdown not found.` | `null` | `null` | `null` | `null` | 0 |
| Known-review unexpected internal action failure before a handled outcome | 500 | `false` | `Task breakdown action failed.` | `null` | self | current id | normalized current status | full durable created-id count before the request |

After Retry or Manual success, React clears the superseded local draft and refetches review state. After Accept success, React clears dirty state and navigates to `next_href`. Any failed response preserves local edits and shows a bounded retryable error without refetch because the specified failure cases do not mutate accepted review state.

### 6. React preserves the full review UX with progressive disclosure

Candidate decision controls, kind, execution mode, title, objective, prompt, acceptance criteria, proof, HITL reason, and constraints remain immediately available. Why-this-task-exists, why-not-smaller/larger, dependencies, and likely entry points use native disclosure. Global contract, global constraints, verification, rejected items, non-goals, recommended sequence, source/model/status/session evidence, and bounded Repo Context evidence remain visible. Failed reviews show Retry, Manual Candidate, and Cancel. Accepted reviews are read-only, show the complete pageable created Task-id evidence, and link to the canonical board rather than presenting misleading editable acceptance controls or inventing nonexistent per-Task detail URLs.

### 7. Unsaved state is browser-local and guarded

The view becomes dirty only after an operator changes editable review state. It registers `beforeunload` only while dirty and intercepts plain in-shell links, browser Back/Forward, Cancel, and action-driven navigation with one confirmation. Confirmed navigation proceeds; canceled navigation restores the current URL/view and retains form state. Modified-click/new-tab behavior remains native. Successful Accept/Retry/Manual clears dirty state before navigation/refetch. No draft is written to the server, local storage, or session storage.

### 8. Verification proves parity from the same review fixtures

Backend tests compare Jinja/shared context and React projection for proposed, failed, accepted, legacy-AFK, project-scoped, and global reviews. Contract tests cover exact nested keys, bounds, redaction-before-truncation, continuations, paging/order, malformed defaults, URL allowlists, auth, `404`, and excluded fields. Mutation tests cover the full HTML/JSON negotiation and status matrix, conflicting concurrent Accept selections with one estimator owner, fail-closed post-claim failures, post-session/pre-Task ambiguity, immutable partial materialization, monotonic revision fencing under a repeated clock, and stale Retry losing to a later accepted state. Frontend tests cover every field, disclosure, failed/accepted states, load-before-edit, all-candidate loading, local-draft preservation, navigation confirmation, and action outcomes. Browser smoke exercises board intake → review → edit → accept → board plus failed Retry/Manual recovery and missing-build Jinja fallback.

## Risks / Trade-offs

- [Many editable fields make the React view dense] → Keep decision-critical fields visible and use native disclosure only for slicing evidence and secondary audit context.
- [Truncation could corrupt accepted work] → Require load-before-edit and omit untouched values so FastAPI retains originals.
- [Navigation guards can fight History API behavior] → Scope guards to the review view, test Back/Forward restoration, and clear them before successful navigation.
- [Retry may complete but produce another failed review] → Treat the mutation as completed, refetch authoritative status, and render the existing safe recovery state.
- [Legacy persisted values may be malformed] → Normalize at the projection boundary without changing the record; backend acceptance validation remains authoritative.
- [Asynchronous Accept, Retry, and Manual requests can race] → Atomically claim one immutable acceptance snapshot with a compare-and-set from `proposed`/`pending_review` to an internal `accepting` state before estimation. Only the claimant may estimate or materialize Tasks; deterministic per-candidate Task ids and metadata-derived linkage preserve partial materialization evidence. Every post-claim failure remains `accepting`, because provider/session side effects may already exist and cannot be safely replayed. Accept progress/finalization plus Retry and Manual writes are fenced by status and a transactionally incremented integer `revision`; `updated_at` remains audit metadata only. An `accepting` claim disables every mutation control and is never time-reclaimed because the estimator/provider has no idempotency hook. Interrupted claims therefore fail closed and require controlled operator repair outside this negotiated action contract. The persistence change is limited to a defaulted Task Breakdown `revision` column.
