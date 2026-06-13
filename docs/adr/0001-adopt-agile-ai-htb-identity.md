# ADR-0001: Adopt AGILE-AI-HTB identity

**Date**: 2026-06-13
**Status**: accepted

## Context

The project started under the descriptive name Token-Tracker Harness. As the portal became the primary demo artifact, the project needed a clearer product identity for operators, judges, and future docs. The name also needed to align package metadata, import paths, the portal, and the local operator command.

The phrase “token-tracker harness” remains useful because it explains what the product does: govern AI coding agents through token-budget guardrails, checkpoints, material handling, and alarms. But using that phrase as the product name makes the artifact feel generic and splits attention from the AGILE-AI-HTB portal brand already present in the mockup.

## Decision

We will use AGILE-AI-HTB as the product, package, import, portal, and operator-command identity, while keeping “token-tracker harness” as the descriptive category.

## Alternatives considered

| Alternative | Pros | Cons | Why rejected |
|---|---|---|---|
| Keep Token-Tracker Harness everywhere | Descriptive; avoids rename churn | Generic product identity; conflicts with portal branding | The demo and packaging need one clear name |
| Use AGILE-AI-HTB only in the portal | Low code churn; preserves existing imports | Splits product identity between UI and code/docs | Future operators would see different names in docs, package metadata, imports, and UI |
| Rename package distribution but keep `token_tracker_harness` imports | Less source churn than full rename | Surprising mismatch between installed package and Python import | The user explicitly chose a full import rename for brand consistency |
| Adopt AGILE-AI-HTB everywhere, keep token-tracker harness as descriptor | Strong product identity; docs remain understandable | Touches source imports, tests, and docs | Accepted trade-off |

## Consequences

- The Python distribution is `agile-ai-htb`.
- The Python import package is `agile_ai_htb`.
- The operator command is `htb`.
- Portal and docs should lead with AGILE-AI-HTB.
- “Token-tracker harness” should appear only as a descriptive phrase or legacy alias, not as the product title.
- No compatibility shim is kept for `token_tracker_harness`; the project is still pre-release/local enough that clean branding is worth the break.
