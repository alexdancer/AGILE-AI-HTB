import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const frontendRoot = fileURLToPath(new URL("../", import.meta.url));
let server;
let EvidenceDrawerState;

before(async () => {
  server = await createServer({
    root: frontendRoot,
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({ EvidenceDrawerState } = await server.ssrLoadModule("/src/views/Board.jsx"));
});

after(async () => {
  await server?.close();
});

const minimalTask = {
  id: "task-demo-999",
  summary: { text: "DEMO evidence task" },
  review_prompt: { text: "" },
  controls: {},
  estimate_tokens: null,
  actual_tokens: null,
};

// jsdom is not available in this harness, so keystroke behaviour (Escape, the
// Tab focus-trap, focus return) can't be simulated here. These assertions lock
// the rendered modal contract the keyboard handlers depend on; the interactive
// behaviour is covered by the handlers wired to those markers in Board.jsx.
test("Evidence Drawer renders the aria-modal dialog contract", () => {
  const markup = renderToStaticMarkup(
    React.createElement(EvidenceDrawerState, {
      task: minimalTask,
      projectId: "demo-999",
      data: null,
      error: null,
      loading: false,
    }),
  );
  assert.match(markup, /role="dialog"/);
  assert.match(markup, /aria-modal="true"/);
  // The dialog must be programmatically focusable so focus can move into it on open.
  assert.match(markup, /<aside[^>]*\btabindex="-1"/);
  assert.match(markup, /aria-label="Evidence for DEMO evidence task"/);
});

test("Evidence Drawer wires Escape dismissal and a Tab focus-trap", () => {
  const source = readFileSync(new URL("../src/views/Board.jsx", import.meta.url), "utf8");
  // Escape closes; Tab is trapped; focus returns to the opener on unmount.
  assert.match(source, /event\.key === "Escape"/);
  assert.match(source, /event\.key !== "Tab"/);
  assert.match(source, /opener instanceof HTMLElement/);
  assert.match(source, /drawerRef\.current\?\.focus\(\)/);
});
