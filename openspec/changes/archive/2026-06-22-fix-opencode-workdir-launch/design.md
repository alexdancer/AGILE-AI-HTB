## Context

The OpenCode comparison demo is intended to prove that the harness can launch a Worker Adapter against `.demo/opencode-comparison/harness-target` while recording native usage. Investigation of the demo database showed the command plan cwd was set to that target, but OpenCode event output referenced and modified `AI-Harness-Token-Tracker/incident-ledger` instead. The direct baseline runbook already uses `opencode run --dir .demo/opencode-comparison/direct-target`, which indicates OpenCode's project root must be passed explicitly, not only via subprocess cwd.

This is a Worker Adapter issue, not a control-plane provider issue. The control-plane/orchestrator model still estimates/routes/reviews. The OpenCode Worker Adapter launches native OpenCode/coding-worker models and imports native usage evidence.

## Goals / Non-Goals

**Goals:**

- Ensure OpenCode native launches are project-root authoritative for the configured adapter workdir.
- Keep the OpenCode command non-interactive: `opencode run --dir <workdir> --model <model> --format json <prompt>`.
- Preserve subprocess cwd as a defensive default while also passing OpenCode's explicit `--dir` argument.
- Record enough post-run evidence to catch the specific failure mode where the process exits 0 but files appear outside the configured target or no configured-target changes are present.
- Keep direct baseline and harness runbook semantics aligned.

**Non-Goals:**

- Do not redesign model routing, token estimation, or control-plane model configuration in this change.
- Do not force all Worker Adapter families to use a `--dir` flag; this is OpenCode-specific unless another adapter has an equivalent project-root option.
- Do not implement proxy runtime throttling for `native_usage`; native usage remains accounting-governed after launch.
- Do not clean or delete misplaced demo files as part of the product fix.

## Decisions

### Decision: OpenCode command planning passes `--dir` explicitly

For adapter `kind == "opencode"`, native verification and native task launch command planning will include `--dir <workdir>` when the adapter has a workdir. The resulting default native launch shape is:

```text
opencode run --dir <workdir> --model <model> --format json <prompt>
```

Rationale: `cwd` controls where the harness starts the process, but OpenCode's own project/session resolution can still choose a different root. `--dir` is the CLI-level contract the direct baseline already relies on.

Alternative considered: only set subprocess cwd. Rejected because the observed demo did exactly that and still wrote elsewhere.

Alternative considered: embed `cd <workdir>` in the prompt. Rejected because the Worker can ignore it, it is not auditable as command-level enforcement, and it contaminates task prompt semantics.

### Decision: Keep cwd and `--dir`

The command plan will continue setting `cwd` to the adapter workdir. The explicit `--dir` is additive, not a replacement.

Rationale: keeping both makes subprocess behavior and OpenCode project resolution agree, and existing tests that assert cwd remains meaningful continue to represent harness process evidence.

### Decision: Normalize defaults, preserve explicit templates carefully

The default OpenCode native launch/verification template should include `--dir` when workdir exists. If a user-supplied `native_launch_template` already contains `--dir`, the harness should not duplicate it. If a user-supplied OpenCode native template omits `--dir`, implementation can either inject it for OpenCode or block launch with a clear compatibility reason; injection is preferred for backward-compatible existing adapter configs.

Rationale: existing DB configs can contain a bare or stale template. The demo should not depend on the operator hand-editing the adapter JSON correctly.

### Decision: Post-run evidence validates configured workdir effects

After a Worker Run exits, the harness should preserve workdir evidence: configured workdir, command cwd, redacted command plan, file/diff evidence for the configured target when available, and suspicious path references extracted from OpenCode JSON events when they are outside the configured workdir. A run that exits 0 but has no configured-target changes while evidence references edits elsewhere should not be treated as completed work for the demo target.

Rationale: native usage evidence proves token accounting, not that useful files landed in the intended target. The product surface should distinguish process success from target-workdir success.

### Decision: The demo requirement is target-specific

The long OpenCode comparison demo should require harness-created files to appear under `.demo/opencode-comparison/harness-target`, not merely somewhere in the repo. That keeps the direct baseline and harness run isolated and comparable.

## Risks / Trade-offs

- [Risk] Existing custom OpenCode templates may already include `--dir` or a different project-root flag. → Mitigation: detect existing `--dir` and avoid duplication; document the normalized default.
- [Risk] OpenCode JSON events may not reliably expose all edited paths. → Mitigation: command-level `--dir` is primary enforcement; path extraction is diagnostic evidence, not the only enforcement mechanism.
- [Risk] Non-git demo target directories make git-diff evidence unavailable. → Mitigation: use filesystem evidence for target directory contents in addition to git porcelain when no git repo exists.
- [Risk] Native usage runs can still exit 0 while the task is incomplete. → Mitigation: this change only catches workdir mismatch; acceptance verification remains the responsibility of task verification/review flows.
- [Risk] Adding `--dir` to verification may cause OpenCode to inspect the target unless prompt forbids it. → Mitigation: keep the sentinel prompt restrictive and retain JSON/native usage evidence checks.
