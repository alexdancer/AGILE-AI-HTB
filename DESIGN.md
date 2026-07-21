---
name: Foreman AI HQ
description: The operator's ledger for governing AI coding agents — a dark, terminal-native control plane.
colors:
  bg-0: "#0b0f12"
  bg-1: "#11171c"
  bg-2: "#161e25"
  bg-3: "#1d2730"
  line: "#243038"
  line-2: "#2d3b46"
  fg-0: "#e6edf3"
  fg-1: "#b3bec8"
  fg-2: "#7d8a96"
  fg-3: "#4f5b66"
  accent: "#5cf2c4"
  accent-dim: "#2a8d72"
  info: "#5cb8f2"
  warn: "#f2c45c"
  danger: "#f25c5c"
  purple: "#b58cf2"
typography:
  display:
    fontFamily: "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, monospace"
    fontSize: "24px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "normal"
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "normal"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif"
    fontSize: "14px"
    fontWeight: 650
    lineHeight: 1.35
    letterSpacing: "normal"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, monospace"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.08em"
rounded:
  sm: "4px"
  md: "6px"
  pill: "999px"
spacing:
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  xxl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.accent-dim}"
    textColor: "{colors.bg-0}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "8px 14px"
  button-primary-hover:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.bg-0}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.fg-1}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "8px 14px"
  button-danger:
    backgroundColor: "transparent"
    textColor: "{colors.danger}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "8px 14px"
  input:
    backgroundColor: "{colors.bg-0}"
    textColor: "{colors.fg-0}"
    rounded: "{rounded.sm}"
    padding: "8px 10px"
  panel:
    backgroundColor: "{colors.bg-1}"
    textColor: "{colors.fg-0}"
    rounded: "{rounded.md}"
    padding: "16px"
  card-task:
    backgroundColor: "{colors.bg-2}"
    textColor: "{colors.fg-0}"
    rounded: "{rounded.md}"
    padding: "14px"
  pill:
    backgroundColor: "{colors.bg-1}"
    textColor: "{colors.fg-1}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "2px 8px"
---

# Design System: Foreman AI HQ

## 1. Overview

**Creative North Star: "The Ledger"**

Foreman AI HQ is honest accounting made visual. Its job is to keep AI coding-agent
work inspectable, so the interface behaves like a ledger an operator can trust: every
token, estimate, and disposition is recorded in a fixed hand, and nothing important is
rounded off or hidden behind a reassuring summary. The surface is a near-black control
plane (`#0b0f12`) with a single mint signal color (`#5cf2c4`) reserved for the things
that are live or actionable. Numbers live in monospace so columns align and totals can
be scanned; prose lives in the system sans. Density is deliberate — a ledger that
omits rows to look calm is a ledger that lies — but every dense surface leads with the
one comparison that matters (estimated versus actual) and lets raw evidence expand from
there.

The register is terminal-native and utilitarian. Chrome is minimal: thin 1px dividers,
flat tonal surfaces, mono labels in small caps. Color is semantic, never decorative —
mint means live/accepted, amber means conserve/attention, red means alarm/blocked, blue
means informational, violet means orchestration spend. The feel is a precision
instrument at rest: the operator is at ease not because the tool is soft, but because
the readouts never lie and escalations only surface what genuinely needs a human.

This system explicitly rejects two things. It is **not a toy AI chat wrapper** — there
is no single magic chat box with launch buttons and no evidence trail; accountability is
the entire point. And it is **not consumer-SaaS hype** — no pastel gradients, no
gradient-accented hero-metric marketing dashboards, no mascots or celebratory confetti.
Softening an operator's console into a growth-marketing aesthetic would undercut the
trust it exists to earn.

**Key Characteristics:**
- Near-black tonal surfaces (`#0b0f12` → `#1d2730`), depth by layering and 1px borders, not shadow
- One mint accent (`#5cf2c4`), rationed to live and actionable elements
- Monospace for every number, identifier, label, and piece of evidence
- Semantic status color (mint / amber / red / blue / violet), always paired with text — never color alone
- Dense by design, with a scanning path: the headline comparison first, raw evidence on demand

## 2. Colors

A near-black control-plane palette: a four-step neutral background ramp, a four-step ink
ramp, one mint accent, and a small set of semantic status hues. Everything is hex sRGB.

### Primary
- **Signal Mint** (`#5cf2c4`): The one voice of the system. Links, active nav, live
  pulse dots, focus rings, progress bars, `green`/accepted pills, and the token chip on
  live events. Reserved for what is live, selected, or actionable — never used as a fill
  for large areas.
- **Muted Teal** (`#2a8d72`): The dimmed accent used as the *fill* for primary buttons
  and selected-option tints, with Signal Mint as the border. Hovering a primary button
  brightens the fill to full Signal Mint.

### Secondary (semantic status)
- **Info Blue** (`#5cb8f2`): Informational notices, `running`/`blue` pills, agent-message
  live events, low-severity alarms.
- **Caution Amber** (`#f2c45c`): Conserve-budget (yellow zone), `warn`/`proposed` pills,
  tool-call live events, nav badge background, blocked-condition and warning notices.
- **Alarm Red** (`#f25c5c`): Red budget zone, `danger`/`failed` pills, danger notices,
  destructive actions, truncation and error text.
- **Orchestration Violet** (`#b58cf2`): The `purple` pill — orchestration spend and
  system categories, kept visually distinct from Worker spend.

### Neutral — Background ramp
- **Void** (`#0b0f12`): The page. Also the text color *on* the mint button, and the
  ground for inputs and the evidence drawer.
- **Panel** (`#11171c`): Panels, sidebar, topbar, KPI tiles, command bars.
- **Raised** (`#161e25`): Panel headers, task cards, dashboard/profile cards, hover
  backgrounds, table header rows.
- **Control** (`#1d2730`): Raised controls (logout, pagination buttons), progress-track
  fills, hover of raised surfaces.

### Neutral — Ink ramp
- **Readout** (`#e6edf3`): Primary text, values, titles.
- **Secondary Ink** (`#b3bec8`): Secondary text, nav labels, body copy inside cards.
- **Muted Ink** (`#7d8a96`): Tertiary/muted text, sub-labels, section labels, disabled-adjacent.
- **Faint Ink** (`#4f5b66`): Faintest text, task IDs, placeholders, inactive markers.

### Neutral — Lines
- **Divider** (`#243038`): Default 1px borders and dividers between rows.
- **Edge** (`#2d3b46`): Stronger 1px borders — input strokes, raised control borders, hover edges.

### Named Rules
**The One Voice Rule.** Signal Mint (`#5cf2c4`) marks only what is live, selected, or
actionable. If mint appears on more than a handful of elements per screen, it has stopped
being a signal. Large regions are never filled with mint — the button fill is Muted Teal,
and mint is the border and the hover.

**The Semantic-Color Rule.** Color is meaning, never decoration. Mint/amber/red/blue/violet
each carry one fixed meaning across the whole product. Never introduce a color for looks,
and never recolor a status hue to fit a layout.

## 3. Typography

**Display / Data Font:** system monospace (`ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, Consolas, monospace`)
**Body Font:** system sans (`-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif`)

**Character:** A two-voice system split by *kind of content*, not by hierarchy level.
Anything countable, identifying, or evidentiary — tokens, IDs, timestamps, labels, status
— is monospace so it aligns in columns and reads as data. Anything conversational — task
descriptions, notice prose, help text — is the system sans. No custom web fonts load; the
stack is deliberately native for speed and terminal familiarity. Base size is 14px at
1.5 line-height.

### Hierarchy
- **Display** (mono, 600, 24px, 1.1): KPI values and headline token figures — the numbers the eye should land on first.
- **Headline** (sans, 600, 18–20px): Page titles and Pipeline / drawer section headings.
- **Title** (sans, 650, 14px, 1.35): Task titles, card headings.
- **Body** (sans, 400, 13–14px, 1.5): Descriptions, notices, help text. Hold long prose to a comfortable measure; don't let evidence text run the full panel width unbroken.
- **Label** (mono, 600, 10–11px, uppercase, 0.08em tracking): Section labels, panel-header titles, pill text, KPI labels, form field labels. The connective tissue of the whole UI.

### Named Rules
**The Numbers-Are-Mono Rule.** Every token count, currency-like figure, identifier,
timestamp, and status label is monospace. A number that appears in the sans body font is
a bug — it breaks column alignment and reads as prose instead of data.

**The Small-Caps-Label Rule.** Structural labels are mono, ~10–11px, uppercase, with
0.06–0.12em tracking. This is the product's signature label voice; use it for panel
headers, section labels, and pills — not for readable body content, which stays sans and
mixed-case.

## 4. Elevation

Flat by default. Depth comes from a four-step tonal background ramp (`bg-0` → `bg-3`) and
1px borders (`line`, `line-2`), not from shadows. A panel sits above the page because it
is one step lighter and outlined, not because it casts a shadow. This keeps the surface
calm and instrument-like and avoids the soft, floating look of consumer SaaS cards.

### Shadow Vocabulary
- **Overlay lift** (`box-shadow: -20px 0 50px rgb(0 0 0 / 35%)`): The *only* real shadow
  in the system — the Evidence Drawer sliding in from the right, over a `rgb(0 0 0 / 58%)`
  backdrop. Reserved for the modal drawer that must read as floating above everything else.

### Named Rules
**The Flat-Ledger Rule.** Surfaces are flat and outlined at rest. Layer with the tonal
ramp and borders, never with drop shadows. The single exception is the Evidence Drawer
overlay; nothing else in the product casts a shadow.

## 5. Components

Terminal-native and utilitarian: thin borders, flat fills, mono labels, tight radii
(4–6px), no ornament.

### Buttons
- **Shape:** Slightly rounded (6px). Mono label, 12px, 600, 0.04em tracking.
- **Primary:** Muted Teal fill (`#2a8d72`) with a Signal Mint border (`#5cf2c4`) and Void
  text (`#0b0f12`); padding `8px 14px`. Hover brightens the fill to full Signal Mint.
- **Secondary / Ghost:** Transparent fill, Edge border (`#2d3b46`), Secondary Ink text;
  hover raises to `bg-2` with Readout text.
- **Danger:** Transparent fill, Alarm Red border and text; used for destructive actions only.
- **Focus:** 2px Signal Mint outline, 2px offset, on every interactive element.

### Chips / Pills
- **Style:** Mono, 10px, uppercase, 0.08em tracking; fully rounded (999px); 1px border;
  `2px 8px` padding. Default is Edge border on Secondary Ink text.
- **State:** Status variants recolor border *and* text together — `running`/`blue` (Info
  Blue), `green` (mint), `yellow` (amber), `red` (Alarm Red), `purple` (violet). The label
  text always states the status; color reinforces, never replaces it.

### Cards / Containers
- **Panel:** `bg-1` fill, 1px Divider border, 6px radius, with a `bg-2` header strip
  carrying a mono uppercase title. The workhorse container.
- **Task card:** `bg-2` fill, 1px Divider border, 6px radius, `14px` padding; hover shifts
  the fill toward `bg-3` and the border to Edge.
- **KPI tile:** `bg-1` fill, 6px radius, mono label over a large mono value, optional 4px
  progress bar filled with Signal Mint.
- **Shadow Strategy:** None — see Elevation. Depth is tonal + border only.

### Inputs / Fields
- **Style:** Void (`#0b0f12`) ground, 1px Edge stroke, 4px radius, `color-scheme: dark`.
  Numeric/identifier inputs use mono; free-text uses sans. Placeholder is Faint Ink.
- **Focus:** Border shifts to Muted Teal with a matching 1px outline.
- **Disabled:** Muted Ink text on `bg-1`, `not-allowed` cursor.

### Navigation
- **Style:** Vertical sidebar, mono 13px labels in Secondary Ink, each with a transparent
  2px left rail. Hover fills `bg-2`. **Active** turns the label mint, fills `bg-2`, and
  lights the left rail mint. Section groups are tiny mono uppercase labels in Faint Ink.
- **Badge:** A `Needs You` count rides an amber (`#f2c45c`) rounded badge with Void text.
- **Mobile:** Below 900px the grid collapses to one column and the sidebar becomes a top strip.

### Live Worker Run feed (signature component)
- One dense mono row per event: a monospace timestamp, a small uppercase kind chip, then
  the event body. The chip color carries the event kind — Info Blue for agent messages,
  Caution Amber for tool calls, Signal Mint for token events — so kind reads where the eye
  already lands, with no side rail. Rows are separated by 1px Dividers. A mint live-pulse
  dot signals an active run and stops animating under reduced-motion.

## 6. Do's and Don'ts

### Do:
- **Do** keep the page near-black (`#0b0f12`) and build depth from the tonal ramp
  (`bg-0`→`bg-3`) plus 1px borders — never drop shadows (the Evidence Drawer overlay is the one exception).
- **Do** set every token count, ID, timestamp, and status label in monospace so columns align.
- **Do** ration Signal Mint (`#5cf2c4`) to live, selected, and actionable elements only — the One Voice Rule.
- **Do** pair every status color with a text label. The green/yellow/red budget zones and
  pass/fail results must never rest on color alone; someone who can't distinguish the hues
  should still read the state.
- **Do** lead dense surfaces with the estimated-versus-actual comparison, then let raw evidence expand on demand.
- **Do** give every interactive element the 2px Signal Mint focus ring and keep launch, review, and disposition actions keyboard-reachable.
- **Do** honor `prefers-reduced-motion`: the live-pulse dot and the estimation progress bar both have static fallbacks — keep it that way for any new motion.

### Don't:
- **Don't** build a toy AI chat wrapper — no single magic chat box with launch buttons and no evidence trail. Accountability is the point; anything that hides what an agent did or cost is the opposite of this product.
- **Don't** drift toward consumer-SaaS hype — no pastel or accent gradients, no gradient-accented hero-metric marketing dashboards, no mascots or celebratory confetti.
- **Don't** use gradient text (`background-clip: text`) or glassmorphism. Emphasis comes from weight, size, and the mint accent, not decorative effects.
- **Don't** fill large regions with Signal Mint. The button fill is Muted Teal (`#2a8d72`); mint is the border and the hover.
- **Don't** introduce a new color for looks, or recolor a status hue (mint/amber/red/blue/violet) to suit a layout — each hue owns one fixed meaning.
- **Don't** set readable body prose in the mono label voice (10–11px uppercase tracked). That voice is for labels and pills; descriptions and help text stay sans and mixed-case.
- **Don't** add drop shadows to cards or panels to make them "pop". Surfaces are flat and outlined at rest.
