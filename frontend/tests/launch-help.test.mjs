import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const frontendRoot = fileURLToPath(new URL("../", import.meta.url));
let server;
let BoardState;

before(async () => {
  server = await createServer({
    root: frontendRoot,
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({ BoardState } = await server.ssrLoadModule("/src/views/Board.jsx"));
});

after(async () => {
  await server?.close();
});

// A launch-ready Estimated card that exercises every guarded launch decision.
function pipelineData() {
  return {
    project: { name: "DEMO 999" },
    workspace: {
      project: { name: "DEMO 999", root_path: "/DEMO/2099", capability: {}, profile: {} },
      summary: { launch_ready: true },
      controls: {},
      links: {},
    },
    needs_you: { count: 0, items: [] },
    board_empty_states: { Estimated: "No Estimated tasks" },
    adapters: [{
      id: "codex",
      name: "Codex",
      is_default: true,
      launchable: true,
      allowed_models: ["gpt-5.4"],
      tracking: { mode: "native_usage", label: "CLI: Track native usage after run" },
    }],
    automation: { queue: { status: "idle" } },
    tasks_by_status: {
      Estimated: [{
        id: "task-est-999",
        status: "Estimated",
        summary: { text: "Estimated DEMO task" },
        estimate_tokens: 100,
        actual_tokens: null,
        recommended_model: "gpt-5.4",
        launch_model: null,
        session_href: null,
        blocked_condition: null,
        controls: {
          can_launch: true,
          requires_manual_estimate: true,
          budget_override_available: true,
          native_usage_override_ack_required: true,
          native_usage_override_ack_text: "Acknowledge native usage overrun risk",
          setup_href: "/settings/workers",
        },
      }],
      Running: [],
      Review: [],
      Done: [],
    },
  };
}

test("launch card explains each consequential decision in plain language", () => {
  const markup = renderToStaticMarkup(
    React.createElement(BoardState, {
      projectId: "demo-999",
      surface: "pipeline",
      data: pipelineData(),
      error: null,
      loading: false,
      action: () => {},
    }),
  );

  // The original control labels are preserved (additive help, not replacement).
  for (const text of ["Approve budget override", "Acknowledge native usage overrun risk", "Manual token estimate"]) {
    assert.match(markup, new RegExp(text));
  }

  // Each decision now carries a plain-language explanation of its consequence.
  assert.match(markup, /Spend tracking · CLI: Track native usage after run/);
  assert.match(markup, /No automatic estimate is available\. Enter the token budget to reserve for this run\./);
  assert.match(markup, /over your remaining budget\. Approving launches it anyway and records an audited budget override\./);
  // renderToStaticMarkup escapes the apostrophe in "can't" (&#x27;), so match past it.
  assert.match(markup, /be throttled mid-run — it may reconcile as an overrun after the run finishes\./);

  // The help is wired to its control for screen readers (aria-describedby ↔ id).
  assert.match(markup, /aria-describedby="budget-override-task-est-999"/);
  assert.match(markup, /id="budget-override-task-est-999"/);
  assert.match(markup, /aria-describedby="native-ack-task-est-999"/);
  assert.match(markup, /aria-describedby="adapter-tracking-task-est-999"/);
});
