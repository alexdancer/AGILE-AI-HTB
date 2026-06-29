# Setup support checklist

Use this when opening a setup issue or asking for help. Do not paste secrets.

## Redacted command output

Run:

```bash
htb check
```

If you are a contributor running from a checkout without installing the CLI, this equivalent development command is also acceptable:

```bash
uv run htb check
```

Paste the redacted `PASS` / `WARN` / `FAIL` output only. Do not paste API keys, portal tokens, `.htb/secrets.env`, bearer tokens, raw credential files, or private repository content.

## Environment details

Include:

- OS and CPU architecture
- Install method: `pipx`, curl installer, Homebrew, source checkout, Docker, or other
- Whether `command -v htb` succeeds
- Control-plane provider/model
- Control-plane key configured through `/settings/control-plane`, `.htb/secrets.env`, or environment variable
- Worker Adapter identity: OpenCode, Claude Code, Codex, Hermes, or other
- Worker tracking status shown in the Portal: verified native usage, diagnostic-only, failed, or unknown
- Whether you are running local Python or Docker

## Boundary reminder

Installing AGILE-AI-HTB exposes the `htb` operator CLI. It does not install or authenticate OpenCode, Claude Code, Codex, Hermes, provider API keys, portal tokens, or Worker credentials. Native Worker CLI setup happens separately in those tools and through the Portal Worker Adapter setup flow.
