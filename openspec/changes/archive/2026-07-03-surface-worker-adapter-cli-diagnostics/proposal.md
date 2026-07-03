## Why

Worker Adapter setup currently can say an adapter is verified while the AGILE Board immediately fails for a project-specific CLI prerequisite, and failed Claude Code verification can hide the actionable root cause behind raw evidence. Operators need the Portal to show local CLI prerequisites such as `Not logged in · Please run /login` and Codex trusted-directory failures as first-class, sanitized setup/launch diagnostics.

## What Changes

- Surface adapter verification CLI failures on `/settings/workers` as primary setup guidance, not only in raw evidence.
- Surface retryable AGILE Board launch failures on the task card with the sanitized CLI stderr/stdout reason and adapter-specific next action.
- Classify common native Worker CLI prerequisite failures, starting with:
  - Claude Code authentication missing: `Not logged in · Please run /login`.
  - Codex project trust failure: `Not inside a trusted directory and --skip-git-repo-check was not specified.`
- Preserve raw diagnostic evidence under existing Advanced/details disclosures while keeping secrets redacted.
- Do not change Worker Adapter tracking semantics, model inventories, token accounting, or OpenCode behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `guided-worker-setup`: Worker Setup primary readiness summaries must include actionable sanitized CLI prerequisite failures such as Claude Code login requirements.
- `board-launch-selection`: AGILE Board task cards must show retryable native Worker launch CLI failures inline with a setup link or adapter-specific next action.
- `worker-adapter-verification`: Verification evidence must preserve a sanitized user-facing failure summary when the native CLI returns an actionable auth/config error.
- `governed-worker-launch`: Worker Run failure evidence must preserve a sanitized user-facing failure summary for native CLI prerequisite failures while keeping the task retryable.

## Impact

- Affected Portal surfaces: `/settings/workers`, AGILE Board task cards, Worker Run/session evidence panels.
- Affected backend paths: adapter verification evidence shaping, launch failure metadata shaping, recoverable Worker Run failure rendering.
- No database schema change required; use existing verification evidence, task metadata, and Worker Run metadata/stdout/stderr fields.
- No dependency changes.
