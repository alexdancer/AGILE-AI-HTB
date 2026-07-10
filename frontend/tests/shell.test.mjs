import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const frontendRoot = fileURLToPath(new URL("../", import.meta.url));
let server;
let Sidebar;
let DashboardState;
let BoardState;
let mergeBoardStatus;
let parseRoute;
let pollBoardStatus;
let submitBoardAction;
let WorkspaceState;
let submitProjectRestore;

before(async () => {
  server = await createServer({
    root: frontendRoot,
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({ Sidebar } = await server.ssrLoadModule("/src/components/Shell.jsx"));
  ({ DashboardState } = await server.ssrLoadModule("/src/views/Dashboard.jsx"));
  ({ BoardState, mergeBoardStatus, pollBoardStatus, submitBoardAction } = await server.ssrLoadModule("/src/views/Board.jsx"));
  ({ WorkspaceState, submitProjectRestore } = await server.ssrLoadModule("/src/views/Workspace.jsx"));
  ({ parseRoute } = await server.ssrLoadModule("/src/App.jsx"));
});

after(async () => {
  await server?.close();
});

function renderSidebar(overrides = {}) {
  const props = {
    activeProjectId: null,
    activeView: "dashboard",
    data: { portal_auth_required: false, sidebar_projects: [] },
    error: null,
    loading: false,
    ...overrides,
  };
  return renderToStaticMarkup(React.createElement(Sidebar, props));
}

function dashboardData(overrides = {}) {
  return {
    next_actions: [{
      label: "Open task board",
      detail: "Estimate, launch, refresh, review, or block tasks",
      href: "/board",
      tone: "green",
    }],
    budget: {
      total_tokens: 150,
      daily_cap: 1_000,
      current_zone: "green",
      since: "2099-01-01T00:00:00+00:00",
    },
    worker_execution: {
      token_total: 150,
      status_split: { completed: 100, failed_retry: 50, unknown: 0 },
      components: { available: true, items: [{ label: "output", value: 50 }], cost: 0.0123 },
    },
    spend: {
      worker_execution: 150,
      agent_review_reporting: 0,
      planning_estimation: 0,
      setup_verification: 0,
      other: 0,
    },
    alarms: {
      total: 1,
      open: 1,
      critical: 0,
      recent: [{
        id: "alarm-demo-999",
        type: "BUDGET_YELLOW",
        severity: "LOW",
        session_id: "sess-demo-999",
        recommended_action: "Review spend.",
      }],
    },
    active_sessions: [{
      id: "sess-demo-999",
      task_description: "DEMO dashboard task",
      model: "opencode/gpt-5.1",
      status: "running",
    }],
    estimation_accuracy: {
      completed_count: 3,
      median_error_ratio: 1.1,
      within_2x_pct: 100,
    },
    projects: [{
      id: "demo-999",
      name: "DEMO 999",
      task_count: 1,
      capability: { state: "launch_ready" },
    }],
    ...overrides,
  };
}

function renderDashboard(state) {
  return renderToStaticMarkup(React.createElement(DashboardState, state));
}

function workspaceData(overrides = {}) {
  return {
    project: {
      id: "demo-999",
      name: "DEMO workspace 999",
      root_path: "/DEMO/2099/repo",
      archived_at: null,
      capability: {
        state: "launch_ready",
        label: "Launch ready",
        reasons: [],
      },
      profile: {
        git_branch: "implementation/demo-999",
        language_hints: ["Python", "JavaScript"],
        framework_hints: ["FastAPI", "React"],
        package_manager_hints: ["uv", "npm"],
        test_command: "uv run pytest",
        run_command: "uv run htb serve",
        relevant_docs: ["README.md", "CONTEXT.md"],
      },
    },
    summary: {
      counts: { Estimated: 1, Running: 2, Review: 3, Done: 4, Blocked: 5 },
      total_tasks: 15,
      launch_ready: true,
      capability_state: "launch_ready",
      attention_actions: [{
        label: "Running work",
        detail: "2 slices need refresh",
        href: "/app/projects/demo-999/board",
        tone: "blue",
      }, {
        label: "Worker setup",
        detail: "Review adapter configuration",
        href: "/settings/workers",
        tone: "yellow",
      }],
    },
    controls: { can_open_board: true, can_restore: false },
    links: {
      board_href: "/app/projects/demo-999/board",
      task_history_href: "/projects/demo-999/task-history",
      sessions_href: "/sessions",
      worker_setup_href: "/settings/workers",
      project_settings_href: "/settings/project",
      restore_href: null,
    },
    ...overrides,
  };
}

function renderWorkspace(state) {
  return renderToStaticMarkup(React.createElement(WorkspaceState, state));
}

function boardData() {
  const emptyStates = Object.fromEntries(
    ["Estimated", "Running", "Review", "Done", "Blocked"].map((status) => [status, `No ${status} tasks`]),
  );
  const detail = {
    task_body: { text: "Full DEMO task body", truncated: false },
    token_components: {
      available: true,
      items: [{ key: "output", label: "Output", value: 21 }],
      cost: 0.01,
      turn_count: 2,
    },
    launch: {
      worker_run_id: "run-demo-999",
      adapter_id: "codex",
      model: "gpt-5.4",
      tracking_mode: "native_usage",
      usage_source: "codex_jsonl",
      status: "completed",
      returncode: 0,
      workdir: "/DEMO/2099",
      error: { text: "", truncated: false },
      blocked_reason: { text: "", truncated: false },
      retryable_failure: { returncode: null, summary: { text: "", truncated: false } },
      diagnostic: {
        summary: { text: "Launch ready", truncated: false },
        next_action: { text: "", truncated: false },
        setup_href: "/settings/workers",
      },
    },
    timeline: [{
      created_at: "2099-01-01T00:00:00Z",
      kind: "worker_completed",
      title: "Worker completed",
      detail_summary: { text: "DEMO timeline detail", truncated: false },
    }],
    logs: {
      stdout: { text: "DEMO stdout", truncated: false },
      stderr: { text: "", truncated: false },
    },
    review: {
      prompt: { text: "Check DEMO contract", truncated: false },
      agent_review: {
        status: "completed",
        recommendation: "accept",
        summary: { text: "Review passed", truncated: false },
        failure: { text: "", truncated: false },
        findings: [{ severity: "info", message: { text: "No defects", truncated: false }, path: null, line: null }],
        review_session_href: "/sessions/review-demo-999",
        model: "openai/gpt-4.1-mini",
        token_total: 34,
      },
    },
    blocked: { reason: { text: "Needs operator input", truncated: false }, requires_manual_estimate: true },
  };
  const card = (status, controls = {}) => ({
    id: `task-${status.toLowerCase()}-999`,
    status,
    summary: { text: `${status} DEMO task`, truncated: false },
    estimate_tokens: 100,
    actual_tokens: status === "Review" ? 89 : null,
    recommended_model: "gpt-5.3",
    launch_model: status === "Review" ? "gpt-5.4" : null,
    session_href: status === "Review" ? "/sessions/session-demo-999" : null,
    controls: {
      can_launch: false,
      can_refresh: false,
      can_save_review_prompt: false,
      can_agent_review: false,
      can_mark_done: false,
      can_block: false,
      can_archive: false,
      can_dismiss: false,
      budget_override_available: false,
      native_usage_override_ack_required: false,
      native_usage_override_ack_text: null,
      setup_href: "/settings/workers",
      ...controls,
    },
    details: detail,
  });
  return {
    project: { id: "demo-999", name: "DEMO 999" },
    columns: ["Estimated", "Running", "Review", "Done", "Blocked"],
    board_summary: {
      launch_ready: true,
      total_tasks: 5,
      counts: { Estimated: 1, Running: 1, Review: 1, Done: 1, Blocked: 1 },
      archived_count: 0,
      history_total_tasks: 5,
    },
    history_href: "/projects/demo-999/task-history",
    board_empty_states: emptyStates,
    automation: {
      counts: { Estimated: 1, Running: 1, Review: 1, Done: 1, Blocked: 1 },
      eligible_count: 1,
      queue: { status: "idle", auto_agent_review: false, latest_stop_reason: null },
      live_refresh_enabled: true,
    },
    adapters: [{
      id: "codex",
      name: "Codex",
      is_default: true,
      launchable: true,
      allowed_models: ["gpt-5.4"],
      tracking: { mode: "native_usage", label: "CLI: Track native usage after run" },
    }],
    tasks_by_status: {
      Estimated: [card("Estimated", {
        can_launch: true,
        can_dismiss: true,
        budget_override_available: true,
        native_usage_override_ack_required: true,
        native_usage_override_ack_text: "Acknowledge native usage overrun risk",
      })],
      Running: [card("Running", { can_refresh: true })],
      Review: [card("Review", {
        can_save_review_prompt: true,
        can_agent_review: true,
        can_mark_done: true,
        can_block: true,
      })],
      Done: [card("Done", { can_archive: true })],
      Blocked: [card("Blocked", { can_archive: true })],
    },
  };
}

test("only exact React routes are parsed as owned views", () => {
  assert.deepEqual(parseRoute("/app"), { view: "dashboard" });
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

test("Dashboard is the sole active home navigation item", () => {
  const markup = renderSidebar();
  assert.match(markup, /class="active" href="\/app">Dashboard/);
  assert.doesNotMatch(markup, /sidebar-action active/);
});

test("dashboard renders loading, error, populated, and empty states", () => {
  const loading = renderDashboard({ data: null, error: null, loading: true });
  assert.match(loading, /Loading dashboard…/);

  const failed = renderDashboard({ data: null, error: new Error("offline"), loading: false });
  assert.match(failed, /Could not load dashboard: offline/);
  assert.match(failed, /href="\/dashboard"/);

  const populated = renderDashboard({ data: dashboardData(), error: null, loading: false });
  assert.match(populated, /Daily governed budget/);
  assert.match(populated, /Worker token component breakdown/);
  assert.match(populated, /href="\/board"/);
  assert.match(populated, /href="\/app\/projects\/demo-999"/);
  assert.match(populated, /href="\/app\/projects\/demo-999\/board"/);
  assert.match(populated, /href="\/sessions\/sess-demo-999"/);

  const empty = renderDashboard({
    data: dashboardData({
      next_actions: [],
      alarms: { total: 0, open: 0, critical: 0, recent: [] },
      active_sessions: [],
      estimation_accuracy: { completed_count: null, median_error_ratio: null, within_2x_pct: null },
      projects: [],
    }),
    error: null,
    loading: false,
  });
  assert.match(empty, /No active sessions/);
  assert.match(empty, /No open alarms/);
  assert.match(empty, /Not enough completed tasks for accuracy tracking/);
  assert.match(empty, /No projects are connected yet/);
  assert.match(empty, /href="\/settings\/project"/);
});

test("React workspace renders active summary, profile, and route-owned links", () => {
  const markup = renderWorkspace({
    projectId: "demo-999",
    data: workspaceData(),
    error: null,
    loading: false,
  });

  for (const text of [
    "DEMO workspace 999",
    "/DEMO/2099/repo",
    "Worker launch is ready",
    "15 tasks",
    "Launch ready",
    "Running work",
    "2 slices need refresh",
    "Repo profile",
    "implementation/demo-999",
    "Python, JavaScript",
    "FastAPI, React",
    "uv, npm",
    "uv run pytest",
    "uv run htb serve",
    "README.md, CONTEXT.md",
  ]) assert.match(markup, new RegExp(text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  for (const href of [
    "/app/projects/demo-999/board",
    "/projects/demo-999/task-history",
    "/sessions",
    "/settings/workers",
    "/settings/project",
  ]) assert.match(markup, new RegExp(`href="${href.replaceAll("/", "\\/")}"`));
  assert.ok(markup.indexOf("15 tasks") < markup.indexOf("Repo profile"));
  assert.doesNotMatch(markup, /Restore project/);

  const source = fileURLToPath(new URL("../src/views/Workspace.jsx", import.meta.url));
  const sourceText = readFileSync(source, "utf8");
  assert.match(sourceText, /<AppLink className="btn" to=\{links\.board_href\}/);
  assert.match(sourceText, /<a className="btn secondary" href=\{links\.sessions_href\}/);
});

test("React workspace renders safe missing, loading, error, and empty states", () => {
  const loading = renderWorkspace({ projectId: "demo-999", data: null, error: null, loading: true });
  assert.match(loading, /Loading project workspace…/);

  const failed = renderWorkspace({
    projectId: "demo-999", data: null, error: new Error("offline"), loading: false,
  });
  assert.match(failed, /Could not load project workspace: offline/);
  assert.match(failed, /href="\/projects\/demo-999"/);

  const empty = renderWorkspace({ projectId: "demo-999", data: null, error: null, loading: false });
  assert.match(empty, /No project workspace state available/);

  const missingData = workspaceData();
  missingData.project.root_path = "";
  missingData.project.capability = { state: "", label: "", reasons: [] };
  missingData.project.profile = {
    git_branch: null,
    language_hints: [],
    framework_hints: [],
    package_manager_hints: [],
    test_command: null,
    run_command: null,
    relevant_docs: [],
  };
  const missing = renderWorkspace({
    projectId: "demo-999", data: missingData, error: null, loading: false,
  });
  assert.match(missing, /Root path unavailable/);
  assert.match(missing, /Unknown/);
  assert.match(missing, /not detected/);
  assert.match(missing, />none</);
  assert.doesNotMatch(missing, /undefined/);
});

test("archived React workspace is restore-first and preserves evidence links", () => {
  const data = workspaceData();
  data.project.archived_at = "2099-01-01T00:00:00Z";
  data.summary.launch_ready = false;
  data.summary.capability_state = "archived";
  data.controls = { can_open_board: false, can_restore: true };
  data.links.board_href = null;
  data.links.restore_href = "/projects/demo-999/restore";
  const markup = renderWorkspace({
    projectId: "demo-999",
    data,
    error: null,
    loading: false,
    restoreError: "Could not restore project.",
    restoreRetryHref: "/projects",
  });

  assert.match(markup, /Archived project/);
  assert.match(markup, /2099-01-01T00:00:00Z/);
  assert.match(markup, /Restore project/);
  assert.match(markup, /Could not restore project/);
  assert.match(markup, /href="\/projects">Open projects/);
  assert.match(markup, /href="\/projects\/demo-999\/task-history"/);
  assert.match(markup, /href="\/sessions"/);
  assert.doesNotMatch(markup, />Open board</);
  assert.doesNotMatch(markup, /Worker launch is ready/);
});

test("project Restore controller refetches only after bounded success", async () => {
  let successCalls = 0;
  let request;
  const success = await submitProjectRestore({
    url: "/projects/demo-999/restore",
    fetchImpl: async (url, options) => {
      request = { url, options };
      return {
        ok: true,
        json: async () => ({
          ok: true,
          error: null,
          next_href: "/app/projects/demo-999",
          retry_href: null,
          project: { id: "demo-999", archived: false },
        }),
      };
    },
    onSuccess: async () => { successCalls += 1; },
  });
  assert.deepEqual(success, { ok: true, error: null, retryHref: null });
  assert.equal(successCalls, 1);
  assert.equal(request.url, "/projects/demo-999/restore");
  assert.equal(request.options.method, "POST");
  assert.equal(request.options.headers.Accept, "application/json");
  assert.equal(request.options.credentials, "same-origin");

  const longError = "e".repeat(1200);
  const failure = await submitProjectRestore({
    url: "/projects/demo-999/restore",
    fetchImpl: async () => ({
      ok: false,
      json: async () => ({ ok: false, error: longError, retry_href: "/projects" }),
    }),
    onSuccess: async () => { successCalls += 1; },
  });
  assert.equal(failure.ok, false);
  assert.equal(failure.error.length, 1000);
  assert.equal(failure.retryHref, "/projects");
  assert.equal(successCalls, 1);

  const invalid = await submitProjectRestore({
    url: "/projects/demo-999/restore",
    fetchImpl: async () => ({ ok: false, json: async () => { throw new Error("raw body"); } }),
    onSuccess: async () => { successCalls += 1; },
  });
  assert.deepEqual(invalid, {
    ok: false,
    error: "Restore returned an invalid response.",
    retryHref: null,
  });
  assert.equal(successCalls, 1);
});

test("archived React board error routes to workspace Restore only", () => {
  const error = new Error("restore archived project before opening its active board");
  error.status = 409;
  const markup = renderToStaticMarkup(React.createElement(BoardState, {
    projectId: "demo-999", data: null, error, loading: false,
  }));
  assert.match(markup, /Archived project/);
  assert.match(markup, /href="\/app\/projects\/demo-999"/);
  assert.doesNotMatch(markup, /href="\/projects\/demo-999\/board"/);
  assert.doesNotMatch(markup, /Run next|Start queue|Launch/);
});

test("React board renders every governed workflow state and bounded detail", () => {
  const loading = renderToStaticMarkup(React.createElement(BoardState, {
    projectId: "demo-999", data: null, error: null, loading: true,
  }));
  assert.match(loading, /Loading board…/);

  const failed = renderToStaticMarkup(React.createElement(BoardState, {
    projectId: "demo-999", data: null, error: new Error("offline"), loading: false,
  }));
  assert.match(failed, /Could not load board: offline/);
  assert.match(failed, /href="\/projects\/demo-999\/board"/);

  const populated = renderToStaticMarkup(React.createElement(BoardState, {
    projectId: "demo-999",
    data: boardData(),
    error: null,
    loading: false,
    query: "",
    notice: null,
    action: () => {},
  }));
  for (const text of [
    "Short task intake",
    "Auto Agent Review",
    "Run next",
    "Start queue",
    "Filter loaded tasks",
    "Codex",
    "gpt-5.4",
    "Approve budget override",
    "Acknowledge native usage overrun risk",
    "Refresh",
    "Save review prompt",
    "Agent Review",
    "Mark Done",
    "Block",
    "Dismiss",
    "Archive",
    "Estimate: 100",
    "Actual: 89",
    "Run: gpt-5.4",
    "Recommended: gpt-5.3",
    "Output",
    "DEMO timeline detail",
    "2099-01-01T00:00:00Z",
    "worker_completed",
    "No defects",
    "openai/gpt-4.1-mini",
    "Manual estimate required",
    "Session report",
  ]) {
    assert.match(populated, new RegExp(text));
  }
  assert.match(populated, /type="file"/);
  assert.match(populated, /type="checkbox"/);
  assert.match(populated, /href="\/sessions\/review-demo-999"/);

  const emptyData = boardData();
  emptyData.board_summary.total_tasks = 0;
  emptyData.tasks_by_status = Object.fromEntries(
    emptyData.columns.map((status) => [status, []]),
  );
  const empty = renderToStaticMarkup(React.createElement(BoardState, {
    projectId: "demo-999", data: emptyData, error: null, loading: false, action: () => {},
  }));
  for (const status of emptyData.columns) assert.match(empty, new RegExp(`No ${status} tasks`));

  const filtered = renderToStaticMarkup(React.createElement(BoardState, {
    projectId: "demo-999", data: boardData(), error: null, loading: false,
    query: "no-such-task", action: () => {},
  }));
  assert.match(filtered, /0 of 5 visible/);
  assert.match(filtered, /No matching tasks/);
});

test("board action controller negotiates JSON, reloads, reports failures, and navigates", async () => {
  const body = { demo: 999 };
  let reloads = 0;
  let request;
  const notices = [];
  const success = await submitBoardAction({
    url: "/projects/demo-999/run-next",
    body,
    fetchImpl: async (url, options) => {
      request = { url, options };
      return { ok: true, json: async () => ({ ok: true, next_href: null }) };
    },
    navigate: () => assert.fail("successful non-navigation action must not navigate"),
    reload: async () => { reloads += 1; },
    onNotice: (notice) => notices.push(notice),
  });
  assert.equal(success, "reloaded");
  assert.equal(reloads, 1);
  assert.equal(request.url, "/projects/demo-999/run-next");
  assert.equal(request.options.method, "POST");
  assert.equal(request.options.body, body);
  assert.equal(request.options.headers.Accept, "application/json");
  assert.equal(request.options.credentials, "same-origin");
  assert.deepEqual(notices, [null]);

  let destination = null;
  const navigated = await submitBoardAction({
    url: "/projects/demo-999/tasks/estimate-form",
    body,
    fetchImpl: async () => ({
      ok: true,
      json: async () => ({ ok: true, next_href: "/task-breakdowns/demo-999/review" }),
    }),
    navigate: (href) => { destination = href; },
    reload: async () => assert.fail("navigation outcome must not reload"),
    onNotice: () => {},
  });
  assert.equal(navigated, "navigated");
  assert.equal(destination, "/task-breakdowns/demo-999/review");

  let failureNotice;
  const failed = await submitBoardAction({
    url: "/projects/demo-999/queue/start",
    body,
    fetchImpl: async () => ({
      ok: false,
      json: async () => ({ ok: false, error: "Worker setup required", setup_href: "/settings/workers" }),
    }),
    navigate: () => assert.fail("failure outcome must not navigate"),
    reload: async () => { reloads += 1; },
    onNotice: (notice) => { failureNotice = notice; },
  });
  assert.equal(failed, "failed");
  assert.equal(reloads, 2);
  assert.deepEqual(failureNotice, {
    message: "Worker setup required",
    setupHref: "/settings/workers",
  });
});

test("board status controller merges counts, reloads cards, and retains state on errors", async () => {
  const current = {
    data: {
      project: { id: "demo-999" },
      automation: { counts: { Estimated: 1 }, queue: { status: "idle" }, live_refresh_enabled: true },
    },
    error: null,
    loading: false,
  };
  let updater;
  const mergedResult = await pollBoardStatus({
    getStatus: async () => ({
      counts: { Estimated: 0, Running: 1 },
      queue: { status: "running" },
      has_active_runs: true,
      queue_active: false,
      reload_required: false,
    }),
    reload: async () => assert.fail("summary-only status must not reload cards"),
    update: (callback) => { updater = callback; },
  });
  assert.equal(mergedResult, "merged");
  const merged = updater(current);
  assert.equal(merged.data.project.id, "demo-999");
  assert.deepEqual(merged.data.automation.counts, { Estimated: 0, Running: 1 });
  assert.deepEqual(merged.data.automation.queue, { status: "running" });
  assert.equal(merged.data.automation.live_refresh_enabled, true);
  assert.deepEqual(mergeBoardStatus({ data: null }, { counts: {} }), { data: null });

  let reloads = 0;
  const reloadedResult = await pollBoardStatus({
    getStatus: async () => ({ reload_required: true }),
    reload: async () => { reloads += 1; },
    update: () => assert.fail("reload-required status must not merge stale cards"),
  });
  assert.equal(reloadedResult, "reloaded");
  assert.equal(reloads, 1);

  const retainedResult = await pollBoardStatus({
    getStatus: async () => { throw new Error("offline"); },
    reload: async () => assert.fail("failed polling must retain current state"),
    update: () => assert.fail("failed polling must retain current state"),
  });
  assert.equal(retainedResult, "retained");
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
