from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Sequence

DEMO_SESSION_ID = "session_2099_demo_claude"
DEMO_STEP_DELAY_SECONDS = 1.2

# Token counts are declared per step and summed for the authoritative result, so
# the provisional lines the operator watches stream in always add up to the
# final total recorded on completion.
_INPUT_TOKENS = (60, 30, 30)
_OUTPUT_TOKENS = (12, 18, 18)


def stream_payloads(model: str, prompt: str) -> list[dict[str, Any]]:
    """Return the synthetic Claude Code `stream-json` payloads, in wire order.

    Every shape here is one the real `claude -p --output-format stream-json`
    emits, so the payloads travel the production adapter path
    (`ClaudeCodeAdapterBuilder.map_stream_event`) rather than a demo-only seam.
    """
    steps: list[dict[str, Any]] = [
        {"type": "system", "subtype": "init", "session_id": DEMO_SESSION_ID, "model": model},
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": f"DEMO reading the repo to plan: {prompt[:120]}"}]},
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "Read", "input": {"file_path": "README.md"}},
                ]
            },
        },
        {"type": "result", "usage": {"input_tokens": _INPUT_TOKENS[0], "output_tokens": _OUTPUT_TOKENS[0]}},
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "DEMO drafting the change against the synthetic fixture."}]},
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "Grep", "input": {"pattern": "DEMO", "path": "."}},
                ]
            },
        },
        {"type": "result", "usage": {"input_tokens": _INPUT_TOKENS[1], "output_tokens": _OUTPUT_TOKENS[1]}},
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "DEMO summarizing findings; no files were modified."}]},
        },
        {"type": "result", "usage": {"input_tokens": _INPUT_TOKENS[2], "output_tokens": _OUTPUT_TOKENS[2]}},
    ]
    return [*steps, _final_result(model, steps)]


def _final_result(model: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the authoritative completion event from the provisional lines above.

    Only this payload carries `session_id`, `modelUsage`, and a cost, which is
    what lets `parse_native_usage_evidence` bind it as the run's final total.
    Summing the already-emitted provisional usage (rather than restating the
    numbers) keeps the operator-facing promise — "final total recorded on
    completion" — true by construction. Cache counters stay at zero so the
    operator-facing actual equals that sum exactly.
    """
    provisional = [step["usage"] for step in steps if step.get("type") == "result"]
    input_tokens = sum(usage["input_tokens"] for usage in provisional)
    output_tokens = sum(usage["output_tokens"] for usage in provisional)
    return {
        "type": "result",
        "subtype": "success",
        "session_id": DEMO_SESSION_ID,
        "total_cost_usd": 0.02,
        "usage": {
            "input_tokens": input_tokens,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "output_tokens": output_tokens,
        },
        "modelUsage": {
            model: {
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
                "cacheReadInputTokens": 0,
                "cacheCreationInputTokens": 0,
                "costUSD": 0.02,
            }
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="foremanctl demo-worker",
        description="Synthetic Worker that streams Claude Code stream-json events. No provider or API key is used.",
    )
    parser.add_argument("prompt", nargs="?", default="DEMO task", help="Task prompt (ignored beyond being echoed).")
    parser.add_argument("--model", default="claude-sonnet-5", help="Model id echoed into the usage evidence.")
    parser.add_argument("--workdir", default=None, help="Project root. Accepted for parity; never written to.")
    parser.add_argument(
        "--delay-ms",
        type=int,
        default=int(DEMO_STEP_DELAY_SECONDS * 1000),
        help="Pause between streamed events, so the live feed is observable in a browser.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    delay_seconds = max(args.delay_ms, 0) / 1000
    payloads = stream_payloads(args.model, args.prompt)
    for index, payload in enumerate(payloads):
        # Line-buffered stdout would still coalesce behind a pipe, and the whole
        # point of this worker is that each event arrives separately.
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()
        if delay_seconds and index < len(payloads) - 1:
            time.sleep(delay_seconds)
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
