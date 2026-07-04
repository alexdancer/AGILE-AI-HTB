# Contributing

Thanks for helping improve AGILE-AI-HTB. This project is a local,
portal-first governance harness for AI coding agents, so contribution hygiene
matters: changes should be small, reviewable, verified, and aligned with the
Harness vocabulary in `CONTEXT.md`.

## Development principles

- Keep `main` releasable. Do not leave half-finished work on the main branch.
- Prefer small vertical slices over broad rewrites.
- Keep product behavior, demo behavior, and internal architecture clearly
  separated.
- Preserve the distinction between the Control Plane model and Worker Adapter
  model/auth configuration.
- Do not add speculative abstractions or unproven modes to public operator docs.
- Treat test, OpenSpec, and documentation warnings as actionable.

## Issues, branches, and labels

Use GitHub Issues for planned work in
`alexdancer/AI-Harness-Token-Tracker`. Keep issue titles and acceptance
criteria specific enough that a human or agent can verify completion.

Default triage labels:

- `needs-triage` — maintainer needs to evaluate.
- `needs-info` — waiting on reporter.
- `ready-for-agent` — fully specified and ready for an AFK agent.
- `ready-for-human` — needs human implementation or decision.
- `wontfix` — will not be actioned.

For implementation work, use a short-lived branch with a focused name. Avoid
mixing feature work, refactors, formatting, and release prep in one change.

## Before changing code or product docs

1. Read `CONTEXT.md` before changing Harness behavior, Portal copy, workflow,
   OpenSpec artifacts, tests, demo data, or docs that use product terminology.
2. Check whether the change should have an OpenSpec proposal. Behavior,
   workflow, architecture, and terminology changes usually should.
3. Inspect nearby code and tests before editing. Follow existing naming,
   structure, and verification patterns.
4. Confirm any new dependency is necessary and belongs in `pyproject.toml`.

## OpenSpec workflow

This repo uses OpenSpec under `openspec/` for spec-driven changes. Prefer the
OpenSpec CLI instead of guessing artifact paths.

Useful commands:

```bash
openspec list --json
openspec status --change "<change-name>" --json
openspec instructions <artifact-id> --change "<change-name>" --json
openspec instructions apply --change "<change-name>" --json
openspec validate <change-name> --strict
openspec validate --all --strict
```

When implementing an OpenSpec change, mark tasks complete only after the code
and relevant verification have passed.

## Local setup for contributors

Install dependencies and run commands through the repo-managed `uv`
environment:

```bash
uv sync --extra test
uv run htb --help
```

For local product use from a checkout:

```bash
uv run htb init
uv run htb serve
```

More setup detail lives in `docs/GETTING_STARTED.md`, `docs/INSTALL.md`, and
`docs/SETUP_SUPPORT_CHECKLIST.md`.

## Required checks

The canonical contributor test command is the same command CI runs:

```bash
uv run --extra test pytest -q
```

Run focused checks first when they are faster or more relevant, then run the
full suite before calling a code change complete:

```bash
uv run htb --help
uv run --extra test pytest tests/portal tests/api tests/workers -q
uv run --extra test pytest tests/evals -v
uv run --extra test pytest -q
```

For package/release-facing changes, also run the build checks used by CI:

```bash
uv build
uvx twine check dist/*
sh scripts/pipx-install-smoke.sh
```

The disposable `pipx` smoke matches CI's install-path check and is most useful
for release, packaging, installer, and entrypoint changes.

If a full check cannot run, document the exact command attempted, the failure,
and the narrower verification that did pass.

## Definition of Done

A change is done only when:

- The issue or OpenSpec goal is satisfied.
- The diff is focused and easy to review.
- Behavior changes have tests or an explicit reason tests are not practical.
- Relevant targeted checks pass.
- `uv run --extra test pytest -q` passes, or any failure is clearly documented
  as blocked/pre-existing.
- Docs are updated when user-facing behavior, setup, terminology, or release
  behavior changes.
- Generated artifacts, caches, logs, and local state are not accidentally
  committed.
- `git status --short` shows only intentional changes.

## Documentation rules

- Keep `README.md` operator-focused: what the project is and how to use it.
- Keep `CONTEXT.md` as the source of truth for domain vocabulary and product
  architecture terms.
- Keep this file focused on contributor workflow.
- Keep release notes or `CHANGELOG.md` focused on user-visible changes.
- Verify README commands and links when editing public setup docs.
- Do not advertise unproven advanced governance modes in README, getting
  started, demo, or support docs.

## Demo data and public evidence

Demo artifacts must be obviously synthetic end-to-end. Use:

- DEMO banners or labels.
- 2099 dates.
- 999-style IDs.
- `.invalid` emails/domains.
- fake addresses clearly marked as DEMO.
- invariant tests for demo sources where practical.

Do not use real customer data, private repo data, real email addresses, real
tokens, or production-looking identifiers in demo fixtures, screenshots, or
support examples.

## Secrets and local state

Never commit secrets or local runtime state, including:

- `.htb/secrets.env`
- provider API keys
- portal tokens
- bearer tokens
- raw credential files
- private repository contents
- local databases, caches, logs, or build outputs unless intentionally tracked
  as fixtures/evidence

Use redacted `htb check` output for support. If working from a source checkout
without installing the CLI, use:

```bash
uv run htb check
```

## Generated artifacts and cleanup

Generated files should stay ignored unless they are intentional fixtures,
evidence, or release artifacts. Before deleting artifact directories, separate
tracked files from ignored/untracked files:

```bash
git status --short --ignored -- <path>
git ls-files <path>
git clean -fdX <path>
```

Prefer uppercase `-X` for ignored-only cleanup. Do not use broad `rm -rf` or
`git clean -fdx` unless the scope and consequences are explicit.

## Agent-assisted development

This project is designed for governed agent workflows. Agent-ready work should
have:

- a clear task objective;
- acceptance criteria;
- relevant files or likely entry points;
- a smallest proof command;
- known constraints and non-goals;
- whether the task is AFK-safe or requires human-in-the-loop judgment.

Do not ask agents to run broad, ambiguous tasks such as "improve the app"
without slicing the work into independently verifiable changes. Preserve the
global Harness contract and require final acceptance verification for integrated
multi-slice work.

## Pull request checklist

Before opening or merging a PR, confirm:

- [ ] The issue or OpenSpec change is linked when applicable.
- [ ] `CONTEXT.md` terminology is followed.
- [ ] The diff is focused.
- [ ] Tests were added or updated for behavior changes.
- [ ] `uv run --extra test pytest -q` passed or the blocker is documented.
- [ ] Relevant OpenSpec validation passed for spec-driven changes.
- [ ] README/docs/changelog were updated if user-facing behavior changed.
- [ ] No secrets or local `.htb/` state are included.
- [ ] Generated files are intentional.
