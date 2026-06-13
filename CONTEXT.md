# Context

## Harness
**Definition**: The governing framework that wraps a coding agent, providing guardrails, checkpoints, material handling, and alarms.
**Also known as**: Token-Tracker Harness.
**Relationships**: Governs a Worker. Declares Guardrails. Evaluates Checkpoints. Fires Alarms. Exposes Material Handling interfaces.

## Worker
**Definition**: The AI coding agent being governed by the harness — the entity that consumes tokens by making API calls and invoking tools.
**Also known as**: Agent, Coding Agent.
**Properties**: Swappable (Hermes, Claude Code, Codex CLI). Communicates via an OpenAI-compatible API.
**Relationships**: Governed by the Harness. Consumes a Token Budget. Produces Session Artifacts.

## Session
**Definition**: A single invocation of the Worker, bounded by start and end. The harness's primary unit of governance.
**Properties**: Has a token budget, a wall-clock duration, a set of tool invocations, and a zone state (green/yellow/red).
**Relationships**: Belongs to a Project. Consists of Tool Invocations. Evaluated by Checkpoints. Produces a Session Artifact.

## Task
**Definition**: A unit of work from the AGILE Board, with a description and an optional token estimate. Advisory, not enforced by the harness.
**Properties**: Has a description, an estimated token cost, and an actual token cost (populated after the session completes).
**Relationships**: Dispatched to a Session. Resides on the AGILE Board.

## Token Budget
**Definition**: A cap on token consumption, declared at two levels — daily (across all sessions) and per-session.
**Also known as**: Budget, Cap.
**Properties**: Expressed in tokens. When exceeded, triggers an alarm but does not halt the agent.
**Relationships**: Governed by Guardrails G1 and G2. Monitored by Checkpoint C1.

## Guardrail
**Definition**: A declared constraint that the harness enforces on the Worker. Every guardrail is explicit configuration, not implicit behavior.
**Properties**: Has a name, a threshold, and an enforcement action (context injection, alarm, or both). Never hard-stops the agent.
**Relationships**: Declared in the Guardrail Configuration. Enforced by the Proxy Engine. May trigger an Alarm.

## Checkpoint
**Definition**: An explicit pass/fail evaluation that runs at a Session boundary, inspecting the Session Artifact for behavioral signals.
**Properties**: Has explicit criteria, a result (pass/fail), and a timestamp. Stateless — re-evaluatable from the artifact alone.
**Relationships**: Evaluates a Session Artifact. May trigger an Alarm on failure. May escalate to a human.

## Alarm
**Definition**: A structured notification that something the harness governs has deviated from expected bounds.
**Properties**: Has a named type (e.g., BUDGET_RED, LOOP_DETECTED), a severity (LOW/MEDIUM/HIGH), context describing the deviation, and a recommended action.
**Relationships**: Triggered by a Guardrail violation or a Checkpoint failure. Routed to a human via a notification channel.

## Material Handling
**Definition**: The clean interfaces for passing work and results between the User, the Harness, and the Worker.
**Properties**: Comprises the Portal UI (AGILE Board, Dashboard) and the REST API (session management, analytics).
**Relationships**: Accepts Tasks from the User. Dispatches Sessions to the Worker. Returns Session Reports to the User.

## AGILE Board
**Definition**: A visual task planning interface where the User creates tasks, estimates token costs, and tracks completion. Shows daily budget utilization across all tasks.
**Properties**: Columns (Backlog, Estimated, Running, Done). Each task card shows estimated vs. actual tokens. Global budget bar at top.
**Relationships**: Part of Material Handling. Contains Tasks. Feeds estimates into Session dispatch.

## Model Recommendation
**Definition**: The harness's suggested model tier for a given Task, based on task complexity classification with an optional budget-aware downgrade.
**Properties**: Has a complexity class (simple/modest/complex), a recommended model name, and a budget-aware clamp that downgrades when daily budget is low. Pre-selected in the Portal; user can override.
**Relationships**: Produced during Task estimation. Feeds into Session dispatch (which model the agent uses).

## Proxy Engine
**Definition**: The component that intercepts all API calls between the Worker and the LLM provider, counting tokens and injecting guardrail context.
**Properties**: Transparent to the Worker — the Worker points its API base URL at the harness. Extracts token counts from provider `usage` fields.
**Relationships**: Enforces Guardrails. Records Tool Invocations. Feeds the Session Artifact Store.

## Session Artifact
**Definition**: The complete record of a Session — token logs, tool traces, alarm history, guardrail state snapshots, and checkpoint results. Persisted for replay.
**Properties**: A JSON-structured bundle. Stateless checkpoint evaluator can re-read it to re-evaluate with updated thresholds.
**Relationships**: Produced by a Session. Evaluated by Checkpoints. Stored in the Session Artifact Store.

## Budget Zone
**Definition**: A graduated classification of how much of a session's token budget has been consumed — green (normal), yellow (wrap-up signal), or red (alarm).
**Properties**: Thresholds declared in the Guardrail Configuration (e.g., green <60%, yellow <85%, red ≤100%). Drives context injection into the Worker.
**Relationships**: Governed by Guardrail G3. Transitions between zones as tokens are consumed. Triggers BUDGET_YELLOW and BUDGET_RED alarms.

## Escalation
**Definition**: The path by which the harness brings a decision to the human rather than guessing — when an alarm fires or a checkpoint fails.
**Properties**: Delivered as a notification with a deep link to the Portal. Human responds with an action (continue, abort, raise budget).
**Relationships**: Triggered by Alarms and Checkpoint failures. Resolved by human action in the Portal.
