# `login.html` provenance check (task 1.1)

Run before deleting `base.html`, per design Migration Plan step 1 — the last point at which the parent template still exists to compare inheritance against.

## Finding: no surviving original exists

The prior session's open item recorded that a `git checkout` during slice 10 verification clobbered the then-uncommitted `login.html`, and that the committed version at `880b3ad` is a reconstruction rebuilt from a full in-session `cat`.

That clobbered file was never committed and never stashed, so it left no object in the repository:

- `git stash list` — empty.
- `git log --all -- src/foreman_ai_hq/templates/login.html` — two commits only: `bc97762` (the pre-slice-10 template) and `880b3ad` (the reconstruction). No intermediate.
- `git fsck --dangling` — no blob containing login markup. The only dangling blob resembling source is a React component.

A `git checkout` overwrites the working tree without writing the discarded content to the object store, so this is the expected outcome rather than a search failure. **The reconstruction cannot be diffed against what it reconstructs.** No further recovery avenue exists.

## Compensating check: contract fidelity against the pre-slice-10 template

`bc97762:src/foreman_ai_hq/templates/login.html` (17 lines, `{% extends "base.html" %}`) is the last committed state before slice 10. Every operator- and browser-visible contract element in it survives verbatim in the reconstruction:

| Contract element | `bc97762` | `880b3ad` (current) |
|---|---|---|
| Form target | `action="/login" method="post"` | identical |
| Field name | `name="token"` | identical |
| Field type / behavior | `type="password" required autofocus` | identical |
| Field id / label binding | `id="token"` + `for="token"` | identical |
| Title | `Login \| Foreman AI HQ` | identical |
| Heading | `Operator login` | identical |
| Subtitle | `portal token · signed cookie · operator-only controls` | identical |
| Token env reference | `TOKEN_TRACKER_PORTAL_TOKEN` in a `<code>` | identical |
| Submit label | `Open portal` | identical |
| Panel header | `Open portal` | identical |

Deliberate additions from slice 10, all consistent with its archived design: a standalone `<!doctype html>` document with no `{% extends %}`, a local `:root` token block and inline styles, the brand line, the footer, and the `{% if error %}` block that renders the sanitized `_LOGIN_ERROR_MESSAGE` in place of the previous raw `401` JSON.

## Conclusion

The reconstruction is faithful on every element that the login contract, its tests, and the `portal-local-access` spec actually constrain. The residual risk — that some purely cosmetic detail of the clobbered draft differs — is unverifiable by construction and immaterial: the surviving template is the one 858 tests, the retirement rehearsal, and the standalone invariant all execute against. It is self-contained and inherits nothing, which is what `portal-local-access:57-63` requires of it after retirement.

Recorded as closed. The prior session's open item #3 needs no further action.

## Defect found while checking

`login.html:27-28` carries a comment reading "Matches `base.html`'s footer." That reference goes stale the moment `base.html` is deleted. Corrected in task 5.
