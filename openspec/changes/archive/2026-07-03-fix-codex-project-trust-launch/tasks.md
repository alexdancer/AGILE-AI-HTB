## 1. Codex command planning

- [x] 1.1 Locate the shared Codex verification and governed launch command construction paths and document which tests cover each path.
- [x] 1.2 Update Codex native launch command planning to include `codex exec`, `--json`, `--skip-git-repo-check`, `-m {selected_model}`, explicit project root/cwd, and the scoped task prompt.
- [x] 1.3 Update Codex native verification command planning to include `--skip-git-repo-check` when using the shared non-interactive Codex command builder.
- [x] 1.4 Ensure sanitized command evidence records the effective Codex command shape, selected model, tracking mode, and project root/cwd without exposing secrets or full unbounded prompt text.

## 2. Guardrail preservation

- [x] 2.1 Verify disallowed Codex models are still rejected before starting any Codex process.
- [x] 2.2 Verify write-capable tasks still fail existing Harness git repository, branch, and clean working tree guardrails before starting Codex, regardless of `--skip-git-repo-check`.
- [x] 2.3 Verify successful Codex process exits still require run-bound `turn.completed.usage` before recording native usage or moving the task to Review.
- [x] 2.4 Verify missing Codex usage evidence remains a retryable Worker Run/task failure and does not alter adapter tracking authority.

## 3. Regression tests

- [x] 3.1 Add/update Codex adapter command-construction tests for launch and verification command shape, including `--skip-git-repo-check`.
- [x] 3.2 Add/update governed launch tests that simulate a Codex Board launch from a non-git or untrusted connected project path and assert the process command includes the bypass flag after Harness guardrails pass.
- [x] 3.3 Add/update guardrail tests proving write-capable non-git or dirty project launches reject before the Codex process is constructed/launched.
- [x] 3.4 Add/update native usage parser/launch tests proving the bypass flag is not treated as usage evidence and `turn.completed.usage` is still required.

## 4. Verification

- [x] 4.1 Run targeted Codex tests for adapter verification, adapter command construction, launch guardrails, and native usage launch accounting.
- [x] 4.2 Run `openspec validate fix-codex-project-trust-launch --strict`.
- [x] 4.3 Run `uv run pytest` after implementation because the repo requires fresh pytest verification after edits.
- [x] 4.4 If local Codex auth is available, run a bounded manual repro against the previously failing connected project root and confirm the failure no longer stops at `--skip-git-repo-check was not specified`; record sanitized evidence only.

Sanitized live Codex repro evidence: `codex exec --json --skip-git-repo-check --ephemeral --sandbox read-only -m gpt-5.4 --cd <non-git-temp-project> -o <temp-last-message> ***PROMPT_REDACTED:70 chars***` returned code 0, emitted `turn.completed`, wrote `AGILE_AI_HTB_CODEX_TRUST_REPRO_2099`, and stdout/stderr did not contain `--skip-git-repo-check was not specified`.
