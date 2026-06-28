# Worker Adapter setup matrix

Worker Adapters are local coding-agent CLI integrations. Tracking mode is separate from adapter identity.

| Worker Adapter | Worker CLI auth source | Tracking modes | Launchable evidence | Common failure |
|---|---|---|---|---|
| OpenCode | Installed `opencode` CLI config/auth | `native_usage`, `proxy_governed`, `observed_only` | Machine-readable, selected-model-aware, successful-exit, run-bound OpenCode usage evidence; or Harness Proxy token rows | CLI not installed, no model discovery, no allowed models, native usage missing run-bound tokens |
| Claude Code | Installed `claude` CLI config/auth | `native_usage`, `observed_only` | `claude -p --output-format json` or `stream-json --verbose` evidence with usage/cost tied to the run | `claude models` unavailable, budget cap confused with accounting proof, cache tokens omitted |
| Codex | Installed Codex CLI config/auth | `native_usage`, `proxy_governed`, `observed_only` when supported by adapter config | Machine-readable successful-run usage or Harness Proxy token rows | CLI auth missing, non-interactive command shape unavailable, no trustworthy usage evidence |
| Hermes | Installed Hermes CLI/profile config | `native_usage`, `proxy_governed`, `observed_only` when supported by adapter config | Run-bound Hermes usage evidence or Harness Proxy token rows | Wrong profile, missing gateway/tool auth, usage unavailable or not bound to the launched task |

## Tracking modes

| Mode | Board launch | Runtime request guardrails | Accounting authority |
|---|---|---|---|
| `proxy_governed` | Yes, after verification | Yes, through Harness Proxy | Budget-authoritative during the run |
| `native_usage` | Yes, after verification | No mid-run throttling | Budget-authoritative only after trustworthy native usage import |
| `observed_only` | No | No | Diagnostic only |

`observed_only` is useful for PATH checks and diagnostics, but it is not normal AGILE Board launchable.

## Key rule

The control-plane API key from `/settings/control-plane` powers AGILE-AI-HTB estimation, planning, recommendations, and reports. It does not configure OpenCode, Claude Code, Codex, Hermes, or other native Worker CLIs.
