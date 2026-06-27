## Context

The AGILE Board renders all tasks across 5 columns in `board.html`. The template uses Jinja2 loops grouped by status, each card rendered as a `<div class="task">` with description text in `<strong class="task-title">` and metadata in `<p class="task-meta mono">`. No filtering exists — operators scroll through all cards.

The board already has a form for task intake above the columns. Adding a filter input above or beside the columns is a template-only change.

## Goals / Non-Goals

**Goals:**
- Add a text input above board columns that filters cards client-side on keystroke
- Filter by card text content (title + metadata), case-insensitive
- Show match count indicator
- Zero dependencies, zero new routes

**Non-Goals:**
- Server-side search, debounced queries, URL-based filter state
- Filter by specific fields (model, status, token count)
- Animations, transitions, accessibility polish beyond a basic `<input>`

## Decisions

### 1. Client-side filtering via inline `<script>`

Vanilla JS in a `<script>` block at the bottom of `board.html`. No separate `.js` file — the board page is the only consumer.

**Alternative considered:** Separate `.js` file served as static asset → rejected. Overkill for 20 lines. The existing templates already use inline JS for adapter model switching.

### 2. Filter target: `.task` div text content

Each `.task` card is hidden/shown based on whether its `textContent` includes the filter query (lowercased). Cards without `.task` class (column headers, empty states) are unaffected.

**Alternative considered:** Filter by `data-*` attributes → rejected. Requires adding attributes to every card template. Text content matching is simpler and covers description + model + estimate display.

### 3. Match count displayed next to filter input

A `<span>` updated on each keystroke shows "N of M tasks visible". When the filter is empty, the indicator is hidden.

### 4. Empty columns show a light placeholder

When a column has cards but all are filtered-out, show "No matching tasks" in that column. When a column is genuinely empty, show the existing empty state.

## Risks / Trade-offs

- **[Risk] Performance with 100+ cards** → Mitigation: The board is designed for single-project use; typical task count is under 50. `textContent` scanning is sub-millisecond at this scale.
- **[Risk] Filter matches hidden text in `<details>` elements** → Mitigation: Leave as-is for now. `<details>` content is collapsed by default and its text is still relevant search material.
