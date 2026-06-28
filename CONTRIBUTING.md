# Contributing

Keep changes small and spec-aligned.

## Before changing code

- Read `CONTEXT.md` for product vocabulary and architecture.
- For behavior changes, create or update an OpenSpec change under `openspec/changes/`.
- Keep Control Plane model config separate from Worker Adapter model/auth config.
- Do not commit secrets, `.htb/secrets.env`, provider keys, portal tokens, or raw private repo data.

## Local checks

```bash
uv run pytest
openspec validate <change-name> --strict
```

For setup issues, include redacted `htb check` output and follow `docs/SETUP_SUPPORT_CHECKLIST.md`. If you are working from a checkout without installing the CLI, `uv run htb check` is an equivalent contributor command.
