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

const render = (error) =>
  renderToStaticMarkup(
    React.createElement(BoardState, {
      projectId: "demo-999",
      data: null,
      error,
      loading: false,
      onRetry: () => {},
    }),
  );

test("a load failure offers an actionable Retry, announced as an alert", () => {
  const markup = render({ message: "offline", status: 500 });
  assert.match(markup, /Could not load board/);
  assert.match(markup, /role="alert"/);
  assert.match(markup, /<button[^>]*>Retry<\/button>/);
  // The raw error detail is never leaked to the operator.
  assert.doesNotMatch(markup, /offline/);
});

test("a sign-in failure explains the fix and does not offer a pointless Retry", () => {
  const markup = render(Object.assign(new Error("unauthorized"), { status: 401 }));
  assert.match(markup, /Board requires sign-in/);
  assert.doesNotMatch(markup, />Retry</);
});
