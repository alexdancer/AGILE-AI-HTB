## Context

The Control Plane model can be configured to use Anthropic/Claude directly. `htb check` validates the model with a small prompt, but Task Breakdown Agent uses a larger structured-output prompt and currently depends on OpenAI-style JSON mode behavior. Anthropic Messages does not enforce `response_format: {"type":"json_object"}`; in the live diagnosis the configured Claude model returned fenced JSON and hit the default translated Anthropic `max_tokens` value of 1024, causing `TaskBreakdownValidationError: task breakdown returned invalid JSON` on 5/5 runs.

The task-breakdown path already has the right durable failure behavior: failed breakdown records show manual recovery and do not silently create whole-task cards. This change should stabilize the valid Claude path without weakening schema validation or changing recovery semantics.

## Goals / Non-Goals

**Goals:**

- Make direct Anthropic/Claude Task Breakdown Agent responses parse reliably when Claude wraps otherwise valid JSON in a ```json fence.
- Ensure Task Breakdown Agent requests explicitly allow enough output tokens for the existing required review object, avoiding the current implicit 1024-token Anthropic cap.
- Keep the existing `validate_breakdown_result` contract as the source of truth after parsing.
- Add tests that fail on the current Claude failure shape and pass after the fix.

**Non-Goals:**

- No Worker Adapter or Claude Code launch changes.
- No Control Plane connection-test UX or status schema changes.
- No retry loop, prompt rewrite, fallback deterministic Markdown splitter, or automatic whole-task creation.
- No new dependencies or provider SDK adoption.
- No broad changes to token accounting categories; successful breakdown usage remains `task_breakdown` orchestration/control-plane spend.

## Decisions

1. **Parse provider wrappers at the Task Breakdown boundary.**
   - Decision: teach the Task Breakdown Agent response parser to accept a bare JSON object or a single fenced JSON block, then pass the decoded object to existing validation.
   - Rationale: fenced JSON is a provider/model response shape, not a valid breakdown schema. Handling it at the boundary keeps downstream data strict.
   - Alternative rejected: make validation accept strings or partial objects. That would blur parsing and schema validation and weaken failure messages.

2. **Set an explicit Task Breakdown output cap.**
   - Decision: include a higher `max_tokens` value in the Task Breakdown Agent request, scoped to this task-breakdown call.
   - Rationale: the live Claude response needed about 1117 completion tokens for a tiny source after increasing the cap; the current implicit Anthropic default of 1024 can truncate valid JSON. The task-breakdown prompt requires candidates, constraints, verification, rationale, and source metadata, so a larger bounded cap is appropriate.
   - Alternative rejected: globally increase Anthropic default `max_tokens` in `LLMClient`. That would affect unrelated control-plane/proxy requests and may increase spend unexpectedly.

3. **Keep malformed/truncated output as failure.**
   - Decision: do not attempt object extraction from arbitrary prose or repair incomplete JSON.
   - Rationale: task breakdown creates operator-reviewed work candidates; accepting repaired or guessed JSON risks bad cards. Manual recovery already exists.
   - Alternative rejected: regex out the first `{...}` from any answer. This can parse accidental snippets or ignore important surrounding refusal/error text.

4. **Test without live credentials, plus preserve the live repro as diagnosis evidence.**
   - Decision: add deterministic tests with fake LLM responses for fenced JSON and request `max_tokens`; keep live provider smoke as optional/manual evidence, not CI.
   - Rationale: CI should not require Anthropic credentials, but the regression seam should mirror the failure shape observed live.

## Risks / Trade-offs

- **Higher task-breakdown token cap can increase control-plane spend** → Mitigate by scoping the cap to Task Breakdown Agent requests only and preserving budget/usage recording.
- **Fence handling could hide non-JSON provider chatter** → Mitigate by accepting only a single fenced block around the response or bare JSON, then requiring normal schema validation.
- **Some large source texts may still exceed the cap** → Mitigate by keeping explicit failure/manual recovery semantics; future work can add summarization or chunking if live evidence shows it is needed.
- **Anthropic model behavior can vary over time** → Mitigate with parser tests for provider wrapper shapes and validation tests for malformed/truncated output.
