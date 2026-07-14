# Context

## Repository Agent Context
**Definition**: The repo-level operating guidance for coding agents working on Foreman AI HQ.
**Properties**: `AGENTS.md` is the entrypoint for agent workflow instructions, OpenSpec usage, issue-tracker assumptions, triage label vocabulary, and verification commands. `CONTEXT.md` is the single domain glossary for product, architecture, workflow, and terminology changes. Agents should read `CONTEXT.md` before changing Harness behavior, Portal copy, OpenSpec artifacts, tests, demo data, or docs that use product language.
**Relationships**: Guides Worker and human-assisted implementation work. Complements OpenSpec artifacts under `openspec/`; OpenSpec change instructions still control planning and task artifact paths, while this glossary controls canonical domain language.

## Harness
**Definition**: The governing framework that wraps a coding agent, providing guardrails, checkpoints, material handling, and alarms.
**Also known as**: Foreman AI HQ, Token-Tracker Harness.
**Relationships**: Governs a Worker. Declares Guardrails. Evaluates Checkpoints. Fires Alarms. Exposes Material Handling interfaces.

## Portal Recovery Surface
**Definition**: The minimal user-facing fallback that preserves Portal authentication and recovery when the normal operator console cannot load.
**Properties**: Provides only login, load-failure explanation, and recovery guidance. It is not a second operator console and does not duplicate Dashboard, Orchestration Board, Setup, Settings, Session, Alarm, or report workflows.
**Relationships**: Supports the Portal Login Token workflow. Remains available independently of the normal authenticated operator-console frontend.

## Control Plane
**Definition**: The deployable Harness surface that owns the Portal, Orchestration Board, budget governance, orchestration workflows, proxy, token accounting, and reports.
**Properties**: Can run as a hosted service. Coordinates work but does not itself guarantee access to a User's local repository or local coding-agent tools.
**Relationships**: Connects to Execution Backends. Receives Worker traffic through the Proxy Engine only for `proxy_governed` launches. Displays Project Capability.

## Execution Plane
**Definition**: The environment where repository access, Worker Adapter launch, and coding-agent execution actually happen.
**Properties**: May be a Local Runner on the User's machine, a Hosted Workspace/Sandbox, or an analysis-only backend with no launch capability.
**Relationships**: Executes Worker Sessions requested by the Control Plane. Provides Project Capability evidence.

## Execution Backend
**Definition**: A concrete execution mode available to the Harness for a Connected Project.
**Properties**: Supported backend types are Local Runner, Hosted Workspace/Sandbox, and analysis-only. A backend determines whether the project can only be analyzed or can also launch governed Worker Sessions.
**Relationships**: Supplies capabilities to the Control Plane. Must satisfy Launch Guardrails before a Task can run.

## Local Runner
**Definition**: A small process running near the User's local repository that connects to the Control Plane and executes Worker Adapter launches on that machine.
**Properties**: Has access to local repo paths and locally installed coding agents. In all-in-one local mode, it can run as a built-in Execution Backend inside the local Harness process. In hosted mode, it pairs with the hosted Control Plane and reports heartbeat/capabilities. Worker model traffic goes through the Harness Proxy only when the adapter is verified as `proxy_governed`; `native_usage` uses the installed CLI's own auth/config and reports usage after the run.
**Relationships**: An Execution Backend. Makes a Connected Project launch-ready when online, paired, and verified.

## Hosted Workspace
**Definition**: A server-side workspace, usually created from a Git URL, that the Control Plane can use for project analysis and eventually hosted Worker execution.
**Properties**: Initially useful for analysis-ready breakdown and estimation. Requires sandboxing, credentials policy, and Worker Adapter installation before it can become launch-ready.
**Relationships**: An Execution Backend. May support Hosted Sandbox execution in later phases.

## Project Capability
**Definition**: The Harness-visible readiness state of a Connected Project.
**Properties**: States include not connected, analysis-ready, launch-ready via Local Runner, launch-ready via Hosted Workspace/Sandbox, and blocked when no execution backend can satisfy launch requirements. The minimum scale proof is multiple projects or execution backends visible in one Control Plane: at least one launch-ready OpenCode path, one analysis-ready path, and one blocked/non-launchable path.
**Relationships**: Shown in the Portal. Feeds Launch Guardrails and determines whether board tasks can launch or only be estimated. The first implementation slice is a local execution slice that proves OpenCode can be verified and launched with trustworthy token ledger evidence; the current public OpenCode proof uses `native_usage`. `proxy_governed` is architecture-supported only for explicitly proxy-capable adapters and must not be advertised in README/getting-started/operator docs until a stock adapter is proven end-to-end. The first OpenCode launch proof is read-only repo inspection that produces a session report artifact; a tiny docs-only change can follow after that succeeds.

## Repository Cleanliness Guardrail
**Definition**: The launch rule that prevents write-capable Worker Sessions from mixing agent edits with pre-existing user changes.
**Properties**: Read-only sessions may run in a dirty repository. Write-capable sessions require a detected git repository, current branch visibility, and a clean working tree before launch. Write-capable sessions create a task branch before launching the Worker.
**Relationships**: Part of Launch Guardrails. Applies to Local Runner and Hosted Workspace execution backends before write-capable Tasks run.

## Task Branch
**Definition**: The git branch created by the Harness for a write-capable Worker Session.
**Properties**: Named with the task identity, for example foremanctl/task-123-short-title. Created only after the Repository Cleanliness Guardrail passes. Read-only sessions do not create task branches. The Worker edits on this branch, but the Harness owns committing: after configured verification passes, the Harness creates the commit with task/session metadata.
**Relationships**: Belongs to a Task and Worker Session. Shown in the Session Artifact and Portal review flow.

## Harness-Owned Commit
**Definition**: A git commit created by the Harness after a write-capable Worker Session completes and configured verification passes.
**Properties**: The Worker may edit files but should not directly own final git history. Commit requires the Project Profile test command to pass when configured and a Harness-generated git diff review summary. If no test command is configured, verification is marked missing test command and manual approval is required before commit. Commit messages include task/session metadata and behavior-specific summary. If verification fails, changes remain uncommitted for review or retry.
**Relationships**: Created on a Task Branch. Referenced by the Session Artifact and Portal review flow.

## Blocked Worker Session
**Definition**: A Worker Session that cannot continue because of a hard safety, workflow, dependency, or manual blocker rather than a retryable adapter runtime failure.
**Properties**: The Harness preserves logs, token ledger entries when present, failure reason, branch name, and any uncommitted diff. Hard safety examples include read-only project mutation and write-capable verification failure requiring manual intervention. Retryable operational failures such as adapter timeout, nonzero exit, or missing authoritative usage after a launch attempt return the Task to Estimated with launch-error evidence instead of making it Blocked.
**Relationships**: Moves or keeps the Task in Blocked only for hard blockers. Operational launch failures are recorded on the Worker Run and keep the Task relaunchable from Estimated.

## Optional Pull Request
**Definition**: A pull request opened from a Harness-created Task Branch after a Harness-Owned Commit exists.
**Properties**: Not required for the first local execution slice. Available only when a GitHub remote is detected and GitHub CLI authentication is available. The Portal may show an optional Open PR action, but lack of PR capability does not block local branch, commit, or session artifact completion.
**Relationships**: Follows Harness-Owned Commit. References the Task Branch, verification result, and Session Artifact.

## Operator Command
**Definition**: A small administrative entrypoint for starting Foreman AI HQ and preparing demo data, not the product user experience.
**Also known as**: `foremanctl`.
**Properties**: Public operators should install this as a bare command through `pipx`, the curl installer, or a future release channel. Contributor `uv run foremanctl ...` commands are repo-local development conveniences, not the primary public setup path. Current commands include `foremanctl init`, `foremanctl serve`, `foremanctl check`, and `foremanctl seed-demo`.
**Relationships**: Starts the Harness. Initializes Operator Config and Local Secret Storage. Seeds Tasks for the Portal. Does not replace Portal workflows for task, session, alarm, or report management.

## Operator Install
**Definition**: The public installation path that makes the bare `foremanctl` command available outside a source checkout.
**Properties**: Current validated path is `pipx install "git+https://github.com/alexdancer/foreman-ai-hq.git"`; after PyPI release it becomes `pipx install foreman-ai-hq`. The curl installer is a bootstrapper that prefers `uv tool install`, falls back to `pipx install`, verifies `foremanctl` is on `PATH`, and prints `foremanctl init` as the next command. Homebrew is planned but not public until a formula and release checksums are validated.
**Relationships**: Precedes Operator Config. Must not ask for or store API keys, portal tokens, Worker credentials, or native CLI auth.

## Operator Config
**Definition**: The local non-secret configuration created by `foremanctl init` and edited by the Portal for normal local operation.
**Properties**: Stored at `.foreman/config.toml`. Contains non-secret settings such as database path, guardrails path, host, port, portal token env name, control-plane provider/model/base URL/env name, and Local Runner enablement. `foremanctl init` writes `.foreman/` state at the Git repository root when run inside Git, or in the current directory outside Git. Default guardrails are written to ignored `.foreman/guardrails.yaml`; SQLite defaults to `.foreman/harness.db` and is created or migrated by `foremanctl init`. Effective startup precedence is CLI flag, then environment variable, then `.foreman/config.toml`, then built-in default.
**Relationships**: Read by `foremanctl serve` and `foremanctl check`. Updated by Control Plane Settings for non-secret fields. Points to Local Secret Storage for actual secret values.

## Local Secret Storage
**Definition**: Ignored local storage for portal and control-plane secret values in the operator setup path.
**Properties**: Stored at `.foreman/secrets.env`. `foremanctl init` creates a portal token value and a control-plane API-key placeholder. `foremanctl serve` and `foremanctl check` load non-placeholder values. Support output must not include raw `.foreman/secrets.env` contents, API keys, bearer tokens, or portal tokens.
**Relationships**: Supplies the Portal Login Token and Control Plane API Key. Distinct from Operator Config, which stores only env var names and other non-secret settings.

## Portal Login Token
**Definition**: The token used to authenticate to the Portal login screen when portal auth is required.
**Properties**: Default env name is `TOKEN_TRACKER_PORTAL_TOKEN`. `foremanctl init` writes a generated value to ignored `.foreman/secrets.env`. Default loopback `foremanctl serve` skips token login; non-loopback/shared/Docker/headless access keeps token auth unless explicitly disabled. Successful login always opens the Dashboard rather than returning to a previously requested Portal page.
**Relationships**: Protects shared Portal pages. Separate from Control Plane API Key and Worker CLI auth.

## Portal-Managed Control Plane API Key
**Definition**: The normal local setup path where an authenticated operator pastes the control-plane provider API key into `/settings/control-plane` instead of manually editing exports first.
**Properties**: A non-empty submitted key is written only to ignored `.foreman/secrets.env` under the configured control-plane API key env name. Blank submissions preserve the existing key. Portal pages, save responses, connection status, logs, and test evidence must not display the raw key value.
**Relationships**: Configures the Control Plane model connection for estimation, task breakdown, recommendations, summaries, and reports. Does not configure native OpenCode, Claude Code, Codex, or other Worker CLI auth.

## Control Plane Connection Test
**Definition**: The explicit setup proof that the configured control-plane provider/model can be called without launching a Worker.
**Properties**: The Portal test records sanitized success or failure evidence and marks changed settings as needing a fresh test. `foremanctl check` calls the configured model and prints redacted support/readiness output without persisting backend status. A failed test keeps Worker Adapter launch readiness separate; it blocks model-powered control-plane actions, not local board viewing.
**Relationships**: Validates Control Plane settings and Portal-Managed Control Plane API Key. Distinct from Worker Adapter verification.

## Setup Overview
**Definition**: The Portal setup surface that guides operators through the next missing action needed for a governed launch.
**Properties**: Summarizes Control Plane model, Token Budget, Worker Adapter, and Connected Project readiness. It should show the next action plainly, keep advanced diagnostics secondary, and route launch-ready users to the project board. It may claim Ready to launch only when at least one Connected Project is launch-ready; no project or analysis-only capability is not launch readiness.
**Relationships**: Coordinates Operator Config, Control Plane Connection Test, Worker Setup, Token Budget, Connected Project, and Orchestration Board readiness.

## Worker
**Definition**: The AI coding agent being governed by the harness — the entity that consumes tokens by making API calls and invoking tools.
**Also known as**: Agent, Coding Agent.
**Properties**: Swappable (OpenCode, Claude Code, Codex CLI, or another coding-agent harness). May use Harness Proxy traffic, native CLI usage reporting, or non-authoritative process/log observation depending on the selected Worker Adapter Tracking Mode.
**Relationships**: Governed by the Harness. Consumes a Token Budget. Produces Session Artifacts.

## Worker Adapter
**Definition**: The Harness integration that configures, validates, launches, and observes an installed local coding-agent CLI such as OpenCode, Claude Code, Codex, or a custom command.
**Properties**: Has a CLI command, working directory, model discovery path, launch command, supported models, tracking mode, and verification status. First-class Worker Adapter presets include OpenCode, Claude Code, and Codex; custom command support may exist for extensibility but is not the primary demo path. OpenCode is the first verified local Worker Adapter target. Adapter verification must exercise the real CLI launch path with a harmless sentinel prompt; install-only checks are not launch proof. Proxy governance is one tracking mode, not the definition of a Worker Adapter. The Portal may show all first-class adapters even when only one is verified in the current environment; Launch Guardrails keep unverified or non-authoritative adapters non-launchable for governed Tasks.
**Relationships**: Selected by the User before launch. Has a Worker Adapter Tracking Mode. Must pass Launch Guardrails before the Orchestration Board can dispatch a governed Task to a Worker.

## Worker Adapter Tracking Mode
**Definition**: The verified method by which the Harness proves token usage for a Worker Adapter launch.
**Properties**: `proxy_governed` means Worker model traffic flows through the Harness Proxy and is budget-authoritative, but it is an advanced/custom proxy-capable adapter path, not the current stock local operator proof. `native_usage` means the coding-agent CLI emits trustworthy machine-readable token usage evidence and is budget-authoritative when verified. Trustworthy native usage includes the selected model, prompt/input tokens, completion/output tokens, total tokens, exit status, and evidence binding the usage to the launched Worker Run. Approximate, scraped, human-readable, model-less, or unbound usage evidence is not authoritative and leaves the adapter `observed_only`. `observed_only` means the Harness can observe process/log evidence but cannot prove governed token usage, so it is not launchable for governed Tasks from the normal Orchestration Board. Observed-only adapters may run only from a separate Worker Setup diagnostic/test flow that records command started, stdout/stderr, exit code or timeout, detected model if available, and an explicit not-budget-authoritative warning without changing task state or showing a Launch-ready badge.
**Portal labels**: `proxy_governed` displays as **API / Proxy: Governed through Harness Proxy**. `native_usage` displays as **CLI: Track native usage after run**. `observed_only` displays as **CLI: Observe command only**. Portal copy must not use the generic label "Governed" for all launchable adapters; it should separately show launch readiness, tracking label, runtime request guardrail availability, and accounting authority.
**Relationships**: Belongs to a Worker Adapter. Feeds Launch Guardrails, Orchestration Tokens, Worker Session accounting, and Portal launch readiness labels.

## Worker Setup
**Definition**: The user-facing configuration workflow for choosing and validating which Worker Adapters can be launched by the Orchestration Board.
**Properties**: Shows adapter configuration, verification results, launchable status, and the default Worker Adapter. The Settings area is the source of truth; the Orchestration Board displays the selected adapter status and links back to setup when launch is blocked.
**Relationships**: Produces launchable Worker Adapters. Supplies Launch Guardrail evidence for Orchestration Board dispatch.

## Session
**Definition**: A single invocation of the Worker, bounded by start and end. The harness's primary unit of governance.
**Properties**: Has a token budget, a wall-clock duration, a set of tool invocations, and a zone state (green/yellow/red).
**Relationships**: Belongs to a Project. Consists of Tool Invocations. Evaluated by Checkpoints. Produces a Session Artifact.

## Worker Run
**Definition**: The persisted execution attempt created when the Orchestration Board launches an Estimated Task through a Worker Adapter.
**Properties**: Created before the adapter subprocess starts and linked to the Task and Session. Records adapter identity, selected model, tracking mode, redacted command plan metadata, status, stdout/stderr evidence, return code, timeout or error details, and completion timestamps. Runs outside the HTTP request lifecycle so the Portal can return immediately while the Worker continues. Duplicate active Worker Runs for the same Task are rejected or mapped to the existing active run. Successful runs with required evidence move the Task to Review. Retryable operational failures such as timeout, nonzero exit, or missing usage evidence return the Task to Estimated with sanitized launch evidence and keep it relaunchable.
**Relationships**: Belongs to a Task and Session. Produced by Task Launch. Supplies Review evidence, Session Artifact evidence, Token Budget reconciliation, and launch failure diagnostics.

## Task
**Definition**: A user-approved unit of coding work from the Orchestration Board, with a description and an optional token estimate. Advisory, not enforced by the harness.
**Properties**: Has a description, acceptance criteria, an estimated token cost, routed or manually selected Worker model when available, selected/default Worker Adapter at launch, actual token cost (populated after the session completes), and metadata for intake source, launch evidence, review prompts, decisions, and blockers.
**Relationships**: May originate from manual entry, Markdown task intake, Markdown plan import, or long-task decomposition. Dispatched to a Session through a Worker Run. Resides on the Orchestration Board.

## Markdown Task Intake
**Definition**: The board intake path that accepts multi-line Markdown text or an uploaded `.md` task file and turns it into one or more estimated Task cards.
**Properties**: Uploaded `.md` file content takes precedence over pasted text when both are supplied. Empty content and unsupported file types are rejected with a clear validation error. Markdown structure is evidence for task breakdown, not the source of truth for Tasks: checklist items, bullets, headings, constraints, non-goals, and verification notes must be semantically classified before any board Task is created. Markdown intake always shows a Task Breakdown Review before estimation, even when the Task Breakdown Agent decides the Markdown describes one coherent Task. Only accepted single-task decisions or vertical-slice candidates become estimated Task cards. Constraints and verification notes are preserved as candidate task metadata or acceptance criteria, not estimated as standalone work. Deterministic Markdown parsing may supply structure hints to the Task Breakdown Agent, but product intake must not expose or silently use deterministic splitting as a fallback or quick-import mode for creating Tasks.
**Relationships**: Feeds the Task Breakdown Agent and Task Estimation. Used by the long synthetic OpenCode comparison task and ordinary operator-entered Markdown plans.

## Proposed Task Breakdown
**Definition**: A human-reviewed set of smaller candidate Tasks produced from a Markdown plan or oversized task before anything is added to the Orchestration Board.
**Properties**: Uses tracer-bullet vertical slices: each proposed Task should be independently grabbable, narrow, demoable or verifiable on its own, and should cut through the needed product layers rather than splitting work by technical layer. Produced by a Task Breakdown Agent that reads all manual task input and Markdown imports, decides whether the work is a single Task or should be separated into multiple Tasks, and explains the decision. Shows candidate task titles, implementation prompts, acceptance criteria, candidate kind, editable global contract summary, lightweight recommended sequence, whether the slice is human-in-the-loop or autonomous, and rejected non-task items with reasons. Candidate kind distinguishes normal `implementation` slices from `acceptance_verification` slices so the Harness does not infer final verification intent from prose alone; the User may edit candidate kind during Task Breakdown Review, but only to one of those two values. Rejected/non-task items are shown explicitly rather than hidden so the User can see that constraints, non-goals, and verification criteria were preserved or deliberately excluded. Constraints may apply to the whole imported plan or to specific candidate tasks; plan-level/global constraints are the default unless the agent or User scopes them more narrowly. The Task Breakdown Agent writes one global contract summary for the Proposed Task Breakdown; accepted implementation tasks inherit that summary and relevant constraints before Task Estimation, while Acceptance Verification carries both the summary and the full original source contract so it can verify the combined artifact against the original request. Recommended sequence may be preserved as metadata or creation order, but the first product slice does not enforce hard inter-task dependency blocking. The first review UI supports practical editing: accept or reject candidates, edit candidate titles or implementation prompts, edit candidate kind, edit the global contract summary, edit constraints and acceptance criteria text, accept a single-task decision, and submit accepted candidates to Task Estimation. It does not require a full planning editor for splitting, merging, drag reordering, arbitrary field editing, or free-text task taxonomy editing. It does not produce official token estimates or routed Worker model selections. Proposed Task Breakdowns are durable review records, not transient form state: source metadata, source text, candidate tasks, rejected/non-task items, global and candidate-scoped constraints, verification criteria, global contract summary, failure details, created Task links, Task Breakdown Model identity, and linked orchestration token/session evidence are preserved for audit, resume, retry, and debugging. Proposed Task Breakdowns are always reviewed by the User before any candidate becomes an estimated Orchestration Board Task; candidates are not auto-created in the first product slice.
**Task Slicing Policy evidence**: Each candidate carries the Control Plane's slicing rationale: objective, smallest proof path, why the Task exists, why it should not be split smaller, why it should not be merged larger, dependencies, likely repo entry points when available, execution mode (`AFK` or `HITL`), and HITL reason when human input is required. This evidence exists to keep the Orchestration Board small, independently verifiable, and free of speculative setup or horizontal layer Tasks.
**Relationships**: Produced during task intake when the Task Breakdown Agent decides the input is multi-task work. Reviewed and edited by the User on the Task Breakdown Review page rather than as an Orchestration Board column or inline board state. Accepting a breakdown immediately sends accepted candidates to Task Estimation and creates Estimated Orchestration Board Tasks, then returns the User to the Orchestration Board; there is no separate accepted-but-unestimated pseudo-backlog state in the first product slice. Rejected items do not enter the Orchestration Board.

## Task Breakdown Review
**Definition**: The operator page at `/task-breakdowns/{breakdown_id}/review` where a Proposed Task Breakdown is edited and either accepted, retried, or replaced with a manual candidate.
**Properties**: Preserves full editable parity with the durable review record: candidate selection, kind, execution mode, title, objective, prompt, acceptance criteria, proof, constraints, HITL reason, slicing-policy evidence, dependencies, likely entry points, global contract summary, global constraints, verification, rejected items, non-goals, and recommended sequence. Pre-acceptance edits stay browser-local; the page warns before navigation with unsaved edits and persists nothing until the operator chooses `Accept selected and estimate`. Accept, Retry, and Manual Candidate are guarded by a monotonic `revision` counter on the `task_breakdowns` row: each mutation is a compare-and-set on the expected status set and expected revision, and a stale or concurrent submission returns a `409` conflict with a retry link instead of silently double-materializing Tasks. Accepted candidates are created with deterministic, idempotent Task ids derived from the breakdown id and candidate index, so a retried accept after a partial failure cannot create duplicate Tasks. React is the canonical implementation once the frontend build is complete; Jinja remains only as missing/partial-build fallback and parity oracle.
**Relationships**: Operates on a Proposed Task Breakdown. Feeds Task Estimation and the Orchestration Board on acceptance. Failed or invalid Task Breakdown Agent output routes here for retry or manual recovery.

## Task Breakdown Agent
**Definition**: The harness-owned orchestration agent that reads incoming manual task text or Markdown plans and decides whether the work should remain one Task or become a Proposed Task Breakdown.
**Properties**: Uses the Harness direct-provider transport path so its spend is tracked as Orchestration Tokens labeled task breakdown. It uses a separate configurable Task Breakdown Model that may be stronger or more planning-oriented than the Estimator LLM while still remaining part of the control-plane/orchestrator model layer rather than the Worker Adapter model layer. It performs semantic decomposition rather than relying on simple length thresholds. It uses lightweight project context such as language, framework, test command, top-level folders, and project docs rather than inspecting arbitrary source files. It follows tracer-bullet vertical-slice rules and returns either a single-task decision or proposed smaller Tasks for human review. Its quality is evaluated with both product-flow tests and golden decomposition fixtures that assert vertical-slice candidates, constraints, verification criteria, non-goals, and rejected-as-task reasons for realistic Markdown plans. The first product slice invokes it for Markdown uploads, Markdown paste, and clearly oversized plain-text input; short plain-text tasks may go directly to Task Estimation to avoid unnecessary latency and orchestration-token spend. If the Task Breakdown Agent fails or returns invalid structure, the Harness shows an explicit breakdown-failed review/manual recovery screen with retry, manual candidate creation, single manual candidate, or cancel actions; it must not silently fall back to deterministic Markdown splitting or create an oversized Estimated Task from the whole source.
**Task Slicing Policy**: The agent applies a Harness-owned policy before proposing board cards: use the fewest vertical slices that preserve independent Worker execution and objective proof; reject constraints, setup prose, verification notes, non-goals, duplicate bullets, and speculative future-proofing as standalone Tasks; prefer reuse of repo patterns over new abstractions; and mark whether each candidate is `AFK`-launchable or requires `HITL` operator judgment.
**Relationships**: Runs before Task Estimation for Markdown intake and clearly oversized plain text. Produces a Proposed Task Breakdown review for both multi-task work and single-task Markdown decisions; Task Estimation runs only after the User accepts reviewed candidates. Short plain-text tasks may bypass breakdown review and go directly to Task Estimation.

## Acceptance Verification
**Definition**: A final verification-oriented Task in a multi-slice breakdown that proves the accepted slices collectively satisfy the original source contract.
**Properties**: Applies when a Proposed Task Breakdown produces one integrated artifact such as a CLI, app, API, demo, or report. It is auto-proposed by default for integrated-artifact breakdowns, but the User may reject it during Task Breakdown Review when the accepted slices are genuinely independent. It is not a replacement for decomposition and is not a request to run the whole implementation as one Task. It checks the original acceptance criteria, global constraints, verification notes, synthetic-data rules, output contracts, and integration behavior after the implementation slices have landed. It should run the smallest executable proof available, such as tests, CLI smoke checks, API calls, artifact parsing, or invariant scans, then produce human-readable findings. If no executable proof is available, it must label the result manual verification only and explain the evidence gap. It prefers an independently configured Worker Adapter or model so verification is less likely to repeat implementation blind spots, but remains launchable with the same verified Worker Adapter when no independent reviewer is available.
**Relationships**: Proposed by the Task Breakdown Agent as the last recommended Task in a Proposed Task Breakdown when an integrated artifact needs final proof. It is an ordinary estimated Orchestration Board Task with its own Token Budget, Worker Run, and Review Disposition, not a hidden Agent Review or free control-plane check. Individual implementation Tasks may move to Done before Acceptance Verification passes, but the overall Proposed Task Breakdown is not globally accepted until its Acceptance Verification Task reaches Done. Acceptance Verification is recommended last and preserved in sequence metadata, but the first implementation does not hard-block launch order. Failed Acceptance Verification moves to Blocked with findings; the User may manually create or approve follow-up Tasks, but the Harness does not automatically create repair work from failure text. Consumes the original Markdown Task Intake contract and produces evidence for Review Disposition.

## Task Estimation
**Definition**: The LLM-assisted orchestration step where the Harness evaluates a Task before launch and produces a token estimate, complexity classification, confidence, rationale, assumptions, and risk flags.
**Properties**: Uses a harness-owned Estimator LLM distinct from the Worker model and Worker Adapter. Uses the Harness direct-provider transport path so estimator spend is tracked as Orchestration Tokens rather than hidden helper spend. Uses an accepted Task, lightweight project context, current budget context, and complexity policy rather than a full repository scan. Produces structured sizing evidence shown to the User before the Task becomes Estimated. Deterministic adapter-aware model routing runs after estimator validation and chooses or omits the Worker model from the selected/default Worker Adapter's allowed models. The User can override the estimate or model before launch. If the Estimator LLM is unavailable or returns invalid output, the User may enter a manual estimate and model, clearly marked as manual rather than LLM-estimated. The Harness must not silently replace a failed Estimator LLM call with a heuristic product estimate. Manual estimates are launchable when required fields are present and Launch Guardrails pass. Estimator LLM tokens count against the daily budget as orchestration tokens, separate from Worker Session tokens.
**Relationships**: Runs after manual task entry or after the User accepts Proposed Task Breakdown items. Feeds deterministic Model Routing. Successful estimation plus routing places a Task in Estimated; failed or invalid estimation places it in Blocked for manual estimate/model entry, while missing Worker model setup preserves estimate evidence but remains guardrail-blocked before launch. Feeds Launch Guardrails and Session dispatch.

## Spike
**Definition**: A bounded pre-task Worker Session used to inspect enough project context to improve a low-confidence estimate before the real implementation begins.
**Properties**: Requires a launchable Worker Adapter because it is a Worker Session. By default it uses the same Worker Adapter and routed Worker model intended for implementation, but the User may override to a cheaper or faster launchable adapter/model. It has no spike-specific token cap; normal daily and session guardrails still apply. It may inspect files, inspect configuration, and run targeted non-mutating tests or discovery commands, but must not modify production code, run destructive commands, broad test suites without approval, migrations, or commits. Its output is findings, revised estimate, risks, and launch recommendation.
**Relationships**: Triggered by low-confidence Task Estimation or by User choice. Counts against the daily budget as orchestration tokens labeled as spike, not Task actual implementation tokens. Automatically updates the Task estimate, routed Worker model when applicable, confidence, rationale, and risks, then returns the Task to Estimated with an updated-by-spike badge. The User still accepts the estimate and chooses the Worker before Launch.

## Orchestration Tokens
**Definition**: Tokens spent by the Harness itself to plan, estimate, validate, or coordinate work before or around Worker execution.
**Properties**: Count against the daily budget, but are labeled separately from Worker Session tokens so operator overhead does not distort task execution analytics.
**Relationships**: Produced by the Task Breakdown Agent, Task Estimation, Spikes, Worker Adapter verification, Agent Review, and reporting. Persisted token usage is labeled by usage kind such as worker, task breakdown, estimation, spike, adapter verification, or reporting with spend-category metadata when needed. Task Breakdown Agent tokens are labeled as task breakdown, not attached to Task implementation actuals, and shown as orchestration spend. Spike tokens are labeled as spike, not Task implementation actuals. Worker Adapter verification tokens are labeled as adapter verification, not attached to Task actuals, and hidden from the normal task board or marked as system verification. Agent Review/reporting tokens use the control-plane model and remain separate from Worker execution spend. Shown separately from Worker tokens in Portal analytics while still counting toward the daily budget.

## Token Budget
**Definition**: A cap on token consumption, declared at two levels — daily (across all sessions) and per-session.
**Also known as**: Budget, Cap.
**Properties**: Expressed in tokens. Daily budget includes both Worker Session tokens and Orchestration Tokens. Per-session budget applies to Worker Session tokens. Budget state gates new launches before they start, but does not automatically halt a Worker Session mid-task. When an estimate exceeds remaining budget before launch, the User may explicitly approve a budget override; the Session is tagged as a budget override and audited. `native_usage` overrides require explicit acknowledgement that native usage cannot be request-throttled mid-run and may reconcile as an overrun after completion. When exceeded during a running Session, the Harness records the overrun and raises alarms; user/admin manual abort remains available.
**Relationships**: Governed by Guardrails G1 and G2. Monitored by Checkpoint C1.

## Guardrail
**Definition**: A declared constraint that the harness enforces on the Worker. Every guardrail is explicit configuration, not implicit behavior.
**Properties**: Has a name, a threshold, and an enforcement action (context injection, alarm, or both). Never hard-stops the agent. Runtime request governance applies only when the Worker Adapter runs in `proxy_governed` mode and Worker model calls pass through the Harness Proxy. `native_usage` is budget-authoritative for accounting but limited to launch/review governance, preflight budget checks, post-run reconciliation, and alarms after usage is known. `observed_only` is process/log evidence only and is not governed-launchable.
**Relationships**: Declared in the Guardrail Configuration. Enforced by the Proxy Engine for `proxy_governed` sessions and by launch/review reconciliation for `native_usage` sessions. May trigger an Alarm.

## Launch Guardrail
**Definition**: A pre-run rule that prevents a Task from becoming Running unless the Harness can govern and observe the chosen Worker.
**Properties**: Validates that a Worker Adapter is configured, the working directory is valid, the selected model is allowed, and the selected tracking mode has proven budget-authoritative token usage. `proxy_governed` adapters require Harness Proxy session-key wiring. `native_usage` adapters require trustworthy native CLI usage evidence. `observed_only` adapters are not launchable for governed Tasks.
**Relationships**: Gates Orchestration Board launch. Protects the token-tracker promise before a Session starts. Distinct from runtime Guardrails, which constrain Worker behavior during a Session.

## Checkpoint
**Definition**: An explicit pass/fail evaluation that runs at a Session boundary, inspecting the Session Artifact for behavioral signals.
**Properties**: Has explicit criteria, a result (pass/fail), and a timestamp. Stateless — re-evaluatable from the artifact alone.
**Relationships**: Evaluates a Session Artifact. May trigger an Alarm on failure. May escalate to a human.

## Alarm
**Definition**: A structured notification that something the harness governs has deviated from expected bounds.
**Properties**: Has a named type (e.g., BUDGET_RED, LOOP_DETECTED), a severity (LOW/MEDIUM/HIGH), context describing the deviation, and a recommended action. Operator resolution offers only validated actions relevant to that Alarm and Session state, such as Continue, Abort Session, or Raise Budget. Generic raw Guardrail mutation is not a normal Alarm action. Open, resolved, and combined history remain inspectable so resolution is auditable.
**Relationships**: Triggered by a Guardrail violation or a Checkpoint failure. Routed to a human via a notification channel.

## Material Handling
**Definition**: The clean interfaces for passing work and results between the User, the Harness, and the Worker.
**Properties**: Comprises the Portal UI (Orchestration Board, Dashboard) and the REST API (session management, analytics).
**Relationships**: Accepts Tasks from the User. Dispatches Sessions to the Worker. Returns Session Reports to the User.

## Orchestration Board
**Definition**: The user-facing Kanban-style orchestration surface where the User enters or imports coding work, reviews harness estimates, selects a Worker, launches governed work, and tracks completion.
**Properties**: Columns represent orchestration state: Estimated (token estimate and any adapter-compatible Worker model selection produced, launchable once guardrails pass), Running (Worker Session active), Review (Session ended and awaits human review), Done (accepted), and Blocked (estimation failed or task needs human change before launch or continuation). There is no full Scrum/Jira workflow and no normal unestimated Backlog because task intake exists to break down, estimate, and budget token spend. A task with a valid estimate but no verified Worker Adapter remains Estimated with Launch available but guardrail-blocked rather than becoming Blocked. Each task card shows estimated vs. actual tokens, selected or routed Worker model when available, default Worker Adapter with per-task override, and linked Session results. Global budget state is visible while planning and dispatching work.
**Relationships**: Part of Material Handling. Contains Tasks. Produces estimates and adapter-aware Worker model routing evidence. Dispatches Estimated Tasks to a Worker through a Session. Returns Session Reports to the User. Accepts work through manual single-task entry, Markdown plan import with task breakdown, or long-task decomposition into multiple smaller Tasks. Current product docs, demo data, and tests should use the canonical board states; old Backlog language belongs only in clearly historical implementation plans.

## Board Run Queue
**Definition**: A project-scoped Orchestration Board automation mode that launches eligible Estimated Tasks one at a time from `/projects/{project_id}/board`.
**Properties**: Requires an explicit Connected Project, uses the existing Task Launch path and Launch Guardrails, records queue source/status/stop reasons as automation evidence, and never falls back to a global or most-recent project. It launches the next eligible Task only after the active Worker Run reaches a terminal state. It stops on no eligible Tasks, operator stop, launch guardrail failure, budget override requirement, native usage acknowledgement requirement, retryable Worker failure, or hard blocker. It does not auto-approve budgets, auto-mark Done, create repair Tasks, or run cross-project autopilot.
**Relationships**: Operates on the Orchestration Board, Tasks, Worker Runs, Launch Guardrails, Token Budget, and Review Disposition. It is Level 3 automation, not Level 4 autonomous execution.

## Run Automation Policy
**Definition**: The explicit project-board policy recorded with board automation events and queued launches.
**Properties**: Default policy is project-scoped, one active Worker Run at a time, no automatic budget override, no automatic Review disposition, and human-required final disposition. It may enable optional Auto Agent Review, but review output remains advisory evidence. Policy and source metadata are persisted on queue state and launched Tasks so operators can audit whether a launch came from `Run next task` or the Board Run Queue.
**Relationships**: Configures Board Run Queue behavior. Consumed by Worker Run lifecycle refresh and displayed in the Portal run automation panel.

## Auto Review
**Definition**: Optional queue policy that automatically runs Agent Review after a queued Worker Run successfully moves a Task into Review.
**Properties**: Uses the existing Agent Review logic and control-plane/orchestrator model. Stores review success or failure as task review evidence and automation timeline evidence. It never changes Review Disposition, never marks Done, never blocks the Task, and never starts autonomous repair work.
**Relationships**: A policy option for Board Run Queue. Produces Agent Review metadata for Review Disposition while preserving human-only final acceptance or blocking.

## Review Disposition
**Definition**: The operator-controlled workflow for deciding what happens after a successful Worker Run moves a Task into Review.
**Properties**: Review cards expose Agent Review, Mark Done, and Block actions when completed Worker Run or Session evidence is present. The operator may save a review prompt or focus while leaving the Task in Review. Mark Done records an accepted operator decision and moves the Task to Done. Block requires a human-readable reason, records blocked review metadata, and moves the Task to Blocked. Review evidence remains linked to the Task regardless of disposition.
**Relationships**: Follows Worker Run completion. Uses Worker Run, Session, token, launch, and optional operator-focus evidence. Updates Task metadata and Orchestration Board state.

## Agent Review
**Definition**: A control-plane review pass over completed Worker execution evidence, requested by the operator from a Review task card.
**Properties**: Uses the Foreman AI HQ control-plane/orchestrator model, not the Worker Adapter model or Worker auth. Builds the review request from Task description, Worker Run evidence, Session Artifact evidence, token evidence, launch metadata, and the latest operator review prompt when present. Persists review status, model, timestamp, summary, recommendation, findings, and sanitized failure details. Agent Review never automatically moves the Task to Done, Estimated, or Blocked; the operator still chooses the disposition.
**Relationships**: Part of Review Disposition. Consumes Orchestration Tokens/reporting spend and produces review metadata displayed on the Orchestration Board.

## Long OpenCode Comparison Demo
**Definition**: A synthetic DEMO 2099 task that compares direct OpenCode execution against Foreman AI HQ-governed OpenCode execution on the same long coding task.
**Properties**: Uses `demo_tasks/DEMO_2099_LONG_OPENCODE_COMPARISON_TASK.md`. The task builds a local-only `incident-ledger` Python CLI with ingest, list, dedupe, score, report, and export commands. Direct OpenCode usage is preserved as external baseline evidence, while the harness path demonstrates estimate, launch guardrails, budget gate or override acknowledgement, Worker Run evidence, token ledger, alarms, and Review workflow. All demo data must stay obviously synthetic: DEMO markers, 2099 dates, `.invalid` emails, DEMO addresses, and 999-style account IDs, with fake-data invariant tests guarding the demo sources.
**Relationships**: Exercises Markdown Task Intake, Worker Adapter tracking modes, Worker Run lifecycle, Token Budget governance, and Review Disposition without introducing real customer data or real external service calls.

## Model Routing
**Definition**: The harness's deterministic Worker model selection step for a given Task, based on estimator complexity evidence, guardrail model-routing policy, budget-aware downgrade rules, and the selected/default Worker Adapter's allowed model set.
**Properties**: Has a complexity class (simple/modest/complex), a guardrail policy candidate, an optional budget-aware clamp that downgrades when daily budget is low, an allowed-model snapshot, and either an adapter-compatible selected Worker model or an explicit no-model setup state. Pre-selected in the Portal when available; user can override before launch. Does not choose the Worker Adapter.
**Relationships**: Runs after Task Estimation validation. Feeds into Session dispatch as the selected Worker model when available. Launch Guardrails re-check the selected model against the Worker Adapter before launch and block before Worker process start if no compatible model is available.

## Proxy Engine
**Definition**: The component that intercepts all API calls between the Worker and the LLM provider, counting tokens and injecting guardrail context.
**Properties**: Transparent to the Worker — the Worker points its API base URL at the harness. Extracts token counts from provider `usage` fields.
**Relationships**: Enforces Guardrails. Records Tool Invocations. Feeds the Session Artifact Store.

## Session Artifact
**Definition**: The complete record of a Session — token logs, tool traces, alarm history, guardrail state snapshots, and checkpoint results. Persisted for replay.
**Properties**: A JSON-structured bundle. Stateless checkpoint evaluator can re-read it to re-evaluate with updated thresholds.
**Relationships**: Produced by a Session. Evaluated by Checkpoints. Stored in the Session Artifact Store. Rendered to the User as the Session Report.

## Session Report
**Definition**: The operator-facing rendering of a Session Artifact at `/sessions/{session_id}`, plus the `/sessions` list of all Sessions.
**Properties**: Preserves full audit-detail parity: token totals/categories, Worker token components, raw provider usage, budget-zone timeline, Worker Run timeline, Repo Context Brief, Alarms, Checkpoint results, and related Agent Review evidence, with dense/raw evidence collapsed by default rather than omitted. The Sessions list auto-refreshes only while at least one Session is active/running and stops polling once none remain. An active Session Report polls only lightweight freshness metadata (`/api/sessions/{session_id}/freshness`) rather than re-fetching full evidence; new evidence shows a `New session evidence available` notice, and the report replaces its data only after the operator explicitly refreshes. React is the canonical implementation once the frontend build is complete; Jinja remains only as missing/partial-build fallback and parity oracle.
**Relationships**: Rendered from a Session Artifact. Linked from the Orchestration Board, Alarms, Task Breakdown Review, and Agent Review evidence.

## Budget Zone
**Definition**: A graduated classification of how much of the shared daily token budget has been consumed — green (normal), yellow (conserve budget), or red (delivery-only).
**Properties**: Thresholds declared in the Guardrail Configuration (e.g., green <60%, yellow <85%, red ≤100%). Drives graduated governance of the Worker.
**Relationships**: Governed by Guardrail G3. Transitions between zones as daily tokens are consumed. Triggers BUDGET_YELLOW and BUDGET_RED alarms. Distinct from per-session caps, which trigger alarms/checkpoints but do not define the zone.

## Escalation
**Definition**: The path by which the harness brings a decision to the human rather than guessing — when an alarm fires or a checkpoint fails.
**Properties**: Delivered as a notification with a deep link to the Portal. Human responds with a validated action appropriate to the Alarm and Session state, such as continue, abort, or raise budget.
**Relationships**: Triggered by Alarms and Checkpoint failures. Resolved by human action in the Portal.
