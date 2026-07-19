import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

import { createServer } from "vite";

const frontendRoot = fileURLToPath(new URL("../", import.meta.url));
let server;
let mergeBoardLiveEvents;
let mergeLiveEvents;
let drainLiveEvents;
let runSingleFlight;

before(async () => {
  server = await createServer({ root: frontendRoot, appType: "custom", logLevel: "silent", server: { middlewareMode: true } });
  ({ mergeBoardLiveEvents } = await server.ssrLoadModule("/src/views/Board.jsx"));
  ({ mergeLiveEvents } = await server.ssrLoadModule("/src/views/SessionReport.jsx"));
  ({ drainLiveEvents, runSingleFlight } = await server.ssrLoadModule("/src/live-events.js"));
});

after(async () => { await server?.close(); });

test("live Worker events append only to matching running Board and Session Report feeds", () => {
  const current = {
    data: {
      tasks_by_status: {
        Running: [{
          status: "Running",
          session_href: "/sessions/ses_demo_999",
          details: { timeline: [{ id: 1, kind: "status" }] },
        }],
      },
    },
  };
  const incoming = [{ id: 2, created_at: "2099-01-01T00:00:00Z", layer: "worker_harness", kind: "token", title: "Provisional usage", detail_summary: "{\\\"total_tokens\\\": 9}" }];

  const board = mergeBoardLiveEvents(current, "ses_demo_999", incoming);

  assert.equal(board.data.tasks_by_status.Running[0].details.timeline.length, 2);
  assert.equal(board.data.tasks_by_status.Running[0].details.timeline[1].detail_summary.text, incoming[0].detail_summary);
  assert.deepEqual(mergeLiveEvents(incoming, incoming), incoming);
});

test("live event polling drains capped pages before advancing its cursor", async () => {
  const calls = [];
  const appended = [];
  const firstPage = Array.from({ length: 100 }, (_, index) => ({ id: index + 1 }));
  const cursor = await drainLiveEvents({
    sessionId: "ses_demo_999",
    sinceId: null,
    getEvents: async (url) => {
      calls.push(url);
      return calls.length === 1
        ? { events: firstPage, next_since_id: 100, has_more: true }
        : { events: [{ id: 101 }], next_since_id: 101, has_more: false };
    },
    append: (events) => appended.push(...events),
  });

  assert.equal(cursor, 101);
  assert.equal(appended.length, 101);
  assert.match(calls[1], /since_id=100/);
});

test("live event polling does not overlap active drains", async () => {
  const lock = { current: false };
  let started = 0;
  let release;
  const first = runSingleFlight(lock, async () => {
    started += 1;
    await new Promise((resolve) => { release = resolve; });
  });
  const second = runSingleFlight(lock, async () => { started += 1; });

  assert.equal(started, 1);
  release();
  await Promise.all([first, second]);
  assert.equal(lock.current, false);
});
