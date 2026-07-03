## Context

The live diagnosis showed two different local CLI prerequisite failures that the operator needs to see in the Portal:

- Codex adapter verification can pass in `native_usage`, but AGILE Board launch against a task-bound connected project can fail immediately because the Codex CLI rejects the project root as untrusted: `Not inside a trusted directory and --skip-git-repo-check was not specified.`
- Claude Code verification can fail before any model usage because the local non-interactive CLI is not authenticated: `Not logged in · Please run /login`.

The current architecture already records verification evidence, Worker Run stdout/stderr, task launch metadata, and retryable failure state. The gap is presentation and shaping: actionable CLI prerequisite failures are not promoted into primary setup/board UI consistently.

## Goals / Non-Goals

**Goals:**

- Show actionable native Worker CLI auth/config failures on `/settings/workers` without requiring raw JSON inspection.
- Show retryable Board launch CLI prerequisite failures on the affected task card with adapter/model/project context.
- Preserve sanitized raw evidence under existing Advanced/details UI for audit and debugging.
- Keep retryable Worker launch failures retryable; do not move them to Blocked unless an existing hard safety guardrail applies.
- Cover known local failures explicitly: Claude Code login required and Codex trusted-directory rejection.

**Non-Goals:**

- No schema migration; use existing evidence JSON, task metadata, Worker Run records, and rendering view models.
- No change to token accounting, tracking mode authority, model discovery, or allowed-model semantics.
- No automatic CLI login, Codex trust mutation, or writing CLI config files from the Portal.
- No OpenCode behavior change beyond shared sanitized diagnostic rendering if it exits with a similar CLI prerequisite failure.
- No new SPA/AJAX workflow; keep existing server-rendered pages and redirects.

## Decisions

1. **Add a small diagnostic classification layer over existing process evidence.**
   - Extract a sanitized `user_message`, `next_action`, and optional `setup_link` from verification evidence or Worker Run stdout/stderr.
   - Initial classifiers are literal and conservative:
     - Claude Code auth: match `Not logged in` and `/login` in stdout/stderr JSONL or text.
     - Codex trust: match `Not inside a trusted directory` / `--skip-git-repo-check` in stderr/text.
   - Alternative considered: display raw stderr everywhere. Rejected because it leaks noisy output into the primary setup path and misses JSONL stdout-only Claude failures.

2. **Treat diagnostics as presentation/evidence, not launch authority.**
   - Adapter readiness continues to use configured/verified/tracking/model/project checks.
   - Diagnostic text explains why an attempt failed; it does not make an adapter launchable or unlaunchable by itself.
   - Alternative considered: fold CLI trust/auth checks into pre-launch guardrails. Rejected for this slice because Codex trust can be project-specific and the user asked first for visibility on the Portal.

3. **Promote actionable failure summaries into existing Portal surfaces.**
   - `/settings/workers` shows the latest verification failure summary near readiness/next action.
   - The AGILE Board task card shows the latest retryable launch failure summary, return code, selected adapter/model, and connected project root when relevant.
   - Raw stdout/stderr/command evidence remains behind details/advanced sections.
   - Alternative considered: create a new diagnostics page. Rejected as heavier than needed.

4. **Keep secrets redacted and command plans bounded.**
   - Reuse existing redaction helpers for evidence values and command plans.
   - Do not display full prompts, session keys, bearer tokens, API keys, or unbounded stdout/stderr in primary UI.

## Risks / Trade-offs

- [Risk] Literal classifier misses a new CLI wording. → Mitigation: fall back to sanitized generic stderr/stdout summary and raw advanced details.
- [Risk] CLI output may include sensitive paths or tokens. → Mitigation: use existing redaction before persistence/rendering and keep raw blocks bounded.
- [Risk] Codex trust failure is project-specific, while adapter verification is project-independent. → Mitigation: show it as a Board launch diagnostic tied to the task project root, not as proof that Codex verification is invalid globally.
- [Risk] Primary UI becomes noisy. → Mitigation: show one concise actionable summary first; keep raw evidence collapsed.
