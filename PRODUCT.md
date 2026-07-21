# Product

## Register

product

## Platform

web

## Users

The primary user is a solo developer or indie engineer who runs AI coding agents
(OpenCode, Claude Code, Codex) against their own repositories and self-hosts the
local Portal on their own machine. They are technical and comfortable in a
terminal; they are not a dedicated ops or platform team, so the console has to be
legible to one person wearing every hat — planner, budget owner, reviewer, and
final approver.

Their context is a working session at their own machine: a local repo connected,
a Worker CLI installed with its own auth, and a coding task they want run with a
paper trail. The job to be done is to launch agent work they can actually trust —
estimate it before it runs, watch it against a budget, and read the evidence
before accepting the result — without turning a long agent run into one opaque
mega-thread. Success is the operator ending a session able to say what an agent
did, what it cost, and why they accepted or blocked it.

## Product Purpose

Foreman AI HQ is a local, portal-first governance harness that wraps a coding
agent CLI rather than replacing it. It adds a board, budgets, launch guardrails,
token evidence, session reports, and human review around tools the operator
already uses. Work flows from intake through estimation, governed launch, live
Worker Run evidence, and human acceptance, with each slice getting its own scoped
run so plan, budget, and review state survive. Success looks like an operator who
trusts the harness to proceed autonomously on the routine and escalate only the
decisions a human must own.

## Positioning

The console keeps agent work inspectable: it turns long, opaque agent runs into
small governed slices, each with visible estimated-versus-actual tokens and a full
evidence trail, so a human can review and accept work instead of taking it on
faith.

## Brand Personality

Technical, dense, and honest. The voice is that of a careful operator's
instrument, not a marketing surface — it speaks in the product's own vocabulary
(Pipeline, Execution Floor, Worker Run, Needs You) and trusts the reader to follow
it. Density is a feature: evidence, token components, and provenance are shown
rather than hidden behind reassuring summaries. Honesty is the load-bearing trait
— the interface labels synthetic demo data as synthetic, distinguishes a `seed`
coefficient from a `fitted` one, and separates orchestration spend from Worker
spend, because a governance tool that rounds off inconvenient truth defeats its
own purpose. The emotional goal is an operator who feels at ease and trusting:
the harness handles the tedium and surfaces only what genuinely needs a human.

## Anti-references

Not a toy AI chat wrapper: no single magic chat box with launch buttons and no
evidence trail. The entire point is accountability, so anything that hides what an
agent did or what it cost is the opposite of this product.

Not consumer SaaS hype: no rounded pastel gradients, no gradient-accented
hero-metric marketing dashboards, no playful mascots or celebratory confetti. The
surface is an operator's console, and softening it into a growth-marketing
aesthetic would undercut the trust it exists to earn.

## Design Principles

Show, don't reassure. Every claim the console makes — an estimate, a token total,
a readiness state — should be backed by inspectable evidence one click away, not a
summarized number the operator has to trust blind.

Honest labels over flattering ones. Name the provenance and the limits: synthetic
versus real, seed versus fitted, orchestration versus Worker spend, native-usage
versus observed-only. A governance tool earns trust by admitting what it cannot
yet prove.

Escalate only. Default to proceeding autonomously and surface a decision only when
a human must own it. Needs You is a short queue of real decisions, not a firehose;
Alarms warn about a running Worker, and the two must never blur together.

Density with a scanning path. Respect the operator's expertise by showing rich
detail, but lead every dense surface with the one comparison that matters
(estimated versus actual) and let raw evidence expand from there.

One evidence system, no parallel truths. The Evidence Drawer and the Session
Report render the same evidence from one implementation; the board never embeds a
second, drifting copy. Canonical product language stays consistent so the
interface and its operator speak the same dialect.

## Accessibility & Inclusion

Solid accessibility defaults without a formal compliance mandate: aim for WCAG AA
contrast on body text and status colors against the dark surfaces, full keyboard
access to launch, review, and disposition actions, visible focus states, and a
reduced-motion alternative for the live pulse and progress animations. The UI is
intentionally dark-only and mono-heavy; where status is carried by the green /
yellow / red budget zones or pass / fail results, pair color with a text or shape
cue so meaning never rests on color alone.
