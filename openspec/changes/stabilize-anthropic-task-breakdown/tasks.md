## 1. Anthropic request compatibility

- [x] 1.1 Update the Anthropic request translation in `src/agile_ai_htb/llm.py` so Anthropic Messages payloads never include `temperature`.
- [x] 1.2 Preserve OpenAI and OpenAI-compatible request translation behavior, including GPT-5 `max_completion_tokens` handling.
- [x] 1.3 Replace model-prefix-specific temperature tests with provider-wide Anthropic tests covering bare and provider-prefixed Claude model IDs, including `claude-opus-4-8`.

## 2. Task Breakdown timeout diagnostics

- [x] 2.1 Add a Task Breakdown-scoped timeout value or timeout context so Task Breakdown failures can report the timeout seconds used for the provider call.
- [x] 2.2 Update Task Breakdown failure wrapping to include safe diagnostics for model, timeout seconds, source character length, and max output tokens when a provider timeout occurs.
- [x] 2.3 Ensure Task Breakdown failure messages do not include raw source text, prompt content, API keys, secret values, or unredacted request payloads.
- [x] 2.4 Preserve the existing failed review/manual recovery actions: retry, manual candidate creation, single manual candidate creation, and cancel.

## 3. Regression coverage

- [x] 3.1 Add or update LLM adapter unit tests proving all Anthropic payloads omit `temperature` while OpenAI/OpenAI-compatible behavior remains unchanged.
- [x] 3.2 Add Task Breakdown tests for timeout diagnostics using a fake LLM/client failure rather than live provider calls.
- [x] 3.3 Add or update route/UI tests proving failed breakdown records show safe actionable diagnostics and still offer manual recovery.

## 4. Verification

- [x] 4.1 Run `uv run pytest tests/unit/test_llm_adapter.py`.
- [x] 4.2 Run `uv run pytest tests/evals/test_estimator.py -k task_breakdown`.
- [x] 4.3 Run any affected Task Breakdown route/portal tests.
- [x] 4.4 Run `uv run pytest` before marking the OpenSpec tasks complete.
- [x] 4.5 Run `openspec validate stabilize-anthropic-task-breakdown --strict`.
