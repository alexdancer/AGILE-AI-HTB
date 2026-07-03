## Context

The live failure is a Codex CLI preflight issue, not a token parser or model allow-list issue. The installed Codex CLI supports `codex exec --json -m {model}` and exposes `--skip-git-repo-check`, while the failing Board run exits before useful work with:

```text
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

AGILE-AI-HTB already has its own launch guardrails: task/project binding, allowed Worker model selection, write-capable git cleanliness checks, command evidence, retryable failure state, and post-run native usage import. This change makes the Codex command plan compatible with those Harness-owned guardrails instead of letting Codex's implicit git/trust preflight short-circuit otherwise-governed launches.

## Goals / Non-Goals

**Goals:**

- Make Codex native usage Board launches use an explicit task-bound project root and `--skip-git-repo-check`.
- Preserve existing Harness write-capable safety: non-git or dirty write tasks remain blocked before Codex starts.
- Preserve native usage authority: successful Codex launches still need run-bound `turn.completed.usage` evidence.
- Preserve model allow-listing: disallowed Codex models remain rejected before process start.
- Record sanitized command evidence showing the Codex launch shape and selected project root/cwd.

**Non-Goals:**

- No automatic Codex trust-store mutation or local Codex config editing.
- No weakening of write-capable git guardrails, branch creation, test verification, or Harness-owned commit behavior.
- No change to OpenCode or Claude Code launch commands.
- No change to Codex model inventory/allowed model IDs or control-plane/orchestrator provider settings.
- No change to token normalization or budget semantics.

## Decisions

1. **Use Codex's supported bypass flag in Harness-controlled launches.**
   - Codex command planning for native Worker launch should include `--skip-git-repo-check` alongside `exec`, `--json`, and `-m {model}`.
   - Rationale: the Harness already validates the task-bound project and launch safety; Codex's preflight was blocking before the Harness could collect meaningful Worker evidence.
   - Alternative considered: require every connected project to be a git repo. Rejected as too broad for read-only/proof/demo projects, while existing write-capable tasks already have git guardrails.

2. **Pass/project-root semantics stay explicit.**
   - The command plan should set cwd to the task-bound connected project root and use Codex's supported project-root option when appropriate, currently `--cd {project_root}`.
   - Rationale: this mirrors the operator expectation that launching from a project board is like opening Codex in that repo/directory.
   - Alternative considered: rely only on subprocess cwd. Rejected because the CLI has an explicit root flag and evidence is clearer when the root is in the command plan.

3. **Do not convert Codex trust failure into adapter-unverified state.**
   - A project trust failure is project/run-specific. It does not invalidate prior native usage verification for Codex generally.
   - Visibility for any remaining failure belongs to the separate `surface-worker-adapter-cli-diagnostics` change and/or existing retryable launch evidence.

4. **Tests should assert command shape and guardrail preservation.**
   - Unit tests should verify the Codex command includes `exec`, `--json`, `--skip-git-repo-check`, selected model, task prompt, and explicit project root/cwd.
   - Guardrail tests should prove disallowed models and write-capable non-git/dirty repo cases are still rejected before Codex starts.

## Risks / Trade-offs

- [Risk] `--skip-git-repo-check` sounds like a safety bypass. → Mitigation: limit it to Codex CLI's own preflight; keep Harness write-capable git/cleanliness guardrails before process start.
- [Risk] Codex CLI flag names change across versions. → Mitigation: tests encode the currently verified `codex exec --help` flag and failure should surface as sanitized command failure evidence.
- [Risk] A non-git read-only Codex run can inspect but not support Harness commit workflow. → Mitigation: write-capable sessions remain blocked unless existing git prerequisites pass.
- [Risk] Project-specific Codex trust issues may still happen for other reasons. → Mitigation: retain retryable failure evidence and Portal diagnostics rather than silently marking verification successful for that run.
