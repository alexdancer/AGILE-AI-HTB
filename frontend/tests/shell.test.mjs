import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const frontendRoot = fileURLToPath(new URL("../", import.meta.url));
let server;
let Sidebar;
let parseRoute;

before(async () => {
  server = await createServer({
    root: frontendRoot,
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({ Sidebar } = await server.ssrLoadModule("/src/components/Shell.jsx"));
  ({ parseRoute } = await server.ssrLoadModule("/src/App.jsx"));
});

after(async () => {
  await server?.close();
});

function renderSidebar(overrides = {}) {
  const props = {
    activeProjectId: null,
    activeView: "home",
    data: { portal_auth_required: false, sidebar_projects: [] },
    error: null,
    loading: false,
    ...overrides,
  };
  return renderToStaticMarkup(React.createElement(Sidebar, props));
}

test("only exact React routes are parsed as owned views", () => {
  assert.deepEqual(parseRoute("/app"), { view: "home" });
  assert.deepEqual(parseRoute("/app/projects/demo-999"), {
    view: "workspace",
    projectId: "demo-999",
  });
  assert.deepEqual(parseRoute("/app/projects/demo-999/board"), {
    view: "board",
    projectId: "demo-999",
  });
  for (const path of [
    "/app/settings",
    "/app/not-a-migrated-route",
    "/app/projects/demo-999/extra",
    "/app/projects/demo-999/board/extra",
  ]) {
    assert.deepEqual(parseRoute(path), { view: "notFound" });
  }
});

test("home highlights the open-project context", () => {
  const markup = renderSidebar();
  assert.match(markup, /class="sidebar-action active"/);
});

test("loading and errors do not masquerade as an empty project list", () => {
  const loading = renderSidebar({ data: null, loading: true });
  assert.match(loading, /Loading…/);
  assert.doesNotMatch(loading, /No projects/);
  assert.doesNotMatch(loading, />Planning</);

  const failed = renderSidebar({ data: null, error: new Error("offline") });
  assert.match(failed, /Could not load projects/);
  assert.match(failed, /href="\/login"/);
  assert.doesNotMatch(failed, /No projects/);
  assert.doesNotMatch(failed, />Planning</);
});

test("loaded empty navigation shows the empty state and Planning", () => {
  const markup = renderSidebar();
  assert.match(markup, /No projects/);
  assert.match(markup, />Planning</);
  assert.match(markup, /href="\/board"/);
});

test("project and board active states follow the selected route", () => {
  const data = {
    portal_auth_required: false,
    sidebar_projects: [{ id: "demo-999", name: "DEMO 999", task_count: 1 }],
  };
  const workspace = renderSidebar({
    activeProjectId: "demo-999",
    activeView: "workspace",
    data,
  });
  assert.match(workspace, /class="project-item active"/);
  assert.match(workspace, /class="project-board"/);
  assert.doesNotMatch(workspace, /class="project-board active"/);

  const board = renderSidebar({
    activeProjectId: "demo-999",
    activeView: "board",
    data,
  });
  assert.match(board, /class="project-item active"/);
  assert.match(board, /class="project-board active"/);
});

test("task-board and logout controls are conditional", () => {
  const withoutTasks = renderSidebar({
    data: {
      portal_auth_required: false,
      sidebar_projects: [{ id: "demo-999", name: "DEMO 999", task_count: 0 }],
    },
  });
  assert.doesNotMatch(withoutTasks, /class="project-board/);
  assert.doesNotMatch(withoutTasks, /action="\/logout"/);

  const authenticated = renderSidebar({
    data: { portal_auth_required: true, sidebar_projects: [] },
  });
  assert.match(authenticated, /action="\/logout"/);
});
