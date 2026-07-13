import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { act, create } from "react-test-renderer";
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
let SessionsState;
let SessionReportState;
let TaskBreakdownReviewState;
let TaskBreakdownReview;
let submitBreakdownAction;
let buildAcceptForm;
let confirmReviewNavigation;
let preventReviewUnload;
let NavContext;
let NavigationGuardContext;

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
  ({ SessionsState } = await server.ssrLoadModule("/src/views/Sessions.jsx"));
  ({ SessionReportState } = await server.ssrLoadModule("/src/views/SessionReport.jsx"));
  ({
    default: TaskBreakdownReview,
    TaskBreakdownReviewState,
    submitBreakdownAction,
    buildAcceptForm,
    confirmReviewNavigation,
    preventReviewUnload,
  } = await server.ssrLoadModule("/src/views/TaskBreakdownReview.jsx"));
  ({ NavContext, NavigationGuardContext } = await server.ssrLoadModule("/src/nav.jsx"));
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

function evidencePage(items = []) {
  return { items, pagination: { offset: 0, limit: 50, total: items.length, has_more: false, next_href: null } };
}

function sessionBounded(preview, truncated = false) {
  return { preview, truncated, full_href: truncated ? "/api/sessions/sess-demo-999/text/task" : null };
}

function reportData() {
  return {
    session: { id: "sess-demo-999", kind: "Worker Session", task: sessionBounded("DEMO task 2099", true), model: "gpt-5.5", status: "running", started_at: "2099-01-01T00:00:00Z", active: true },
    summary: {
      selected_project: sessionBounded("DEMO project 999"), launch_target: sessionBounded("opencode run"), adapter_id: "opencode", worker_model: "gpt-5.5", tracking_mode: "native_usage", status: "running", result: sessionBounded("Worker running"), requires_review: true,
      missing_labels: ["missing authoritative usage"], evidence_counts: { alarms: 1, checkpoints: 1, failed_checkpoints: 1, worker_runs: 1, worker_events: 1, error_events: 0 },
    },
    tokens: {
      provider_totals: { prompt_tokens: 30, completion_tokens: 20, total_tokens: 50 },
      normalized: { total_tokens: 40, by_category: { control_plane: 1, task_breakdown: 2, worker_execution: 30, adapter_verification: 3, reporting_summary: 4, other: 0 } },
      worker_components: { available: true, items: [{ key: "cache_read", label: "cache read/reused context", value: 10 }, { key: "output", label: "output", value: 20 }], cost: 0.01, turn_count: 1 },
      log: evidencePage([{ usage_kind: "worker", model: "gpt-5.5", prompt_tokens: 30, completion_tokens: 20, total_tokens: 50, cost: 0.01, raw_usage: sessionBounded("provider raw usage", true) }]),
    },
    zone_timeline: evidencePage([{ zone: "yellow", max_tokens: 2048, created_at: "2099-01-01T00:00:01Z" }]),
    worker_timeline: evidencePage([{ created_at: "2099-01-01T00:00:02Z", level: "info", layer: "worker_harness", kind: "launch", title: "Worker launched", detail_summary: "status=running", detail: sessionBounded("timeline detail", true) }]),
    repo_context_briefs: evidencePage([{ worker_run_id: "run-demo-999", documents: evidencePage([{ path: "AGENTS.md" }]), manifests: evidencePage(["pyproject.toml"]), text: sessionBounded("Repo Context Brief text", true) }]),
    alarms: evidencePage([{ id: "alarm-demo-999", type: "BUDGET_YELLOW", severity: "MEDIUM", recommended_action: "Review spend", created_at: "2099-01-01T00:00:03Z" }]),
    checkpoints: evidencePage([{ name: "budget_health", passed: false, details: sessionBounded("checkpoint detail", true) }]),
    related_agent_review: {
      status: "completed", recommendation: "approve", summary: sessionBounded("Agent Review summary", true), model: "claude-demo-999", reviewed_at: "2099-01-01T00:00:04Z", review_session_id: "review-demo-999", review_session_href: "/sessions/review-demo-999", review_total_tokens: 19, error: null,
      findings: evidencePage([sessionBounded("Agent Review finding", true)]),
    },
    freshness: { session_id: "sess-demo-999", status: "running", active: true, version: "a".repeat(64), last_evidence_at: "2099-01-01T00:00:04Z" },
    links: { sessions_href: "/sessions", self_href: "/sessions/sess-demo-999" },
  };
}

test("only exact React routes are parsed as owned views", () => {
  assert.deepEqual(parseRoute("/app"), { view: "dashboard" });
  assert.deepEqual(parseRoute("/sessions"), { view: "sessions" });
  assert.deepEqual(parseRoute("/sessions/sess-demo-999"), {
    view: "sessionReport",
    sessionId: "sess-demo-999",
  });
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

test("Sessions sidebar and list preserve compact scan, states, and pagination", () => {
  const sidebar = renderSidebar({ activeView: "sessions" });
  assert.match(sidebar, /class="active" href="\/sessions">Sessions/);
  assert.doesNotMatch(sidebar, /class="active" href="\/app">Dashboard/);

  const loading = renderToStaticMarkup(React.createElement(SessionsState, { data: null, error: null, loading: true }));
  assert.match(loading, /Loading Sessions/);
  const failed = renderToStaticMarkup(React.createElement(SessionsState, { data: null, error: new Error("secret"), loading: false }));
  assert.match(failed, /Could not load Sessions. Retry/);
  assert.doesNotMatch(failed, /secret/);
  const data = {
    sessions: [{ id: "sess-demo-999", kind: "Agent Review", task_preview: "DEMO review task", model: "claude-demo-999", status: "running", active: true, token_totals: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 }, evidence_counts: { worker_runs: 1, worker_events: 2, failed_checkpoints: 1 }, current_zone: "yellow", alarm_count: 1, report_href: "/sessions/sess-demo-999" }],
    pagination: { offset: 0, limit: 1, total: 2, has_more: true }, has_active: true, poll_after_ms: 5000,
  };
  const populated = renderToStaticMarkup(React.createElement(SessionsState, { data, error: null, loading: false }));
  for (const text of ["Agent Review", "DEMO review task", "claude-demo-999", "10 prompt", "5 completion", "15 total", "1 runs", "2 events", "1 failed checks", "yellow zone", "1 alarms", "Active sessions refresh every 5 seconds", "Next sessions"]) assert.match(populated, new RegExp(text));
  assert.match(populated, /href="\/sessions\/sess-demo-999"/);
});

test("Session Report renders compact governance plus every bounded evidence path", () => {
  const markup = renderToStaticMarkup(React.createElement(SessionReportState, {
    data: reportData(), error: null, loading: false,
    freshnessNotice: { version: "b".repeat(64) },
    refreshError: "Could not check for new session evidence. Retry Refresh.",
  }));
  for (const text of [
    "Governance summary", "DEMO task 2099", "DEMO project 999", "opencode", "native_usage", "review needed", "missing authoritative usage",
    "Provider / raw totals", "Normalized budget total", "control_plane: 1", "worker_execution: 30", "reporting_summary: 4", "cache read/reused context",
    "Token log", "provider raw usage", "Budget-zone timeline", "yellow zone", "Worker Run timeline", "worker_harness", "Repo Context Brief", "AGENTS.md", "pyproject.toml",
    "Alarms", "BUDGET_YELLOW", "Checkpoint results", "FAIL", "Related Agent Review", "review/control-plane evidence", "19 review/control-plane tokens", "Agent Review finding",
    "Preview truncated", "Load full text", "New session evidence available", "Could not check for new session evidence",
  ]) assert.match(markup, new RegExp(text));
  assert.match(markup, /href="\/sessions\/review-demo-999"/);
  assert.match(markup, /aria-live="polite"/);
  assert.ok(markup.indexOf("Governance summary") < markup.indexOf("Token log"));
});

test("Session Report refresh remounts paged evidence and labels review-session outcomes", () => {
  const data = reportData();
  data.session.kind = "Agent Review";
  const markup = renderToStaticMarkup(React.createElement(SessionReportState, { data, error: null, loading: false }));
  assert.match(markup, /Agent Review outcome/);
  const source = readFileSync(new URL("../src/views/SessionReport.jsx", import.meta.url), "utf8");
  for (const key of ["tokens-${version}", "zones-${version}", "worker-${version}", "repo-${version}", "alarms-${version}", "checkpoints-${version}"]) {
    assert.ok(source.includes(key));
  }
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

function bounded(preview, overrides = {}) {
  return { preview, truncated: false, full_href: null, ...overrides };
}

function page(items = []) {
  return {
    items,
    pagination: { offset: 0, limit: 50, total: items.length, has_more: false, next_href: null },
  };
}

function breakdownReviewData(status = "proposed") {
  const candidate = {
    index: 0,
    accepted_by_default: status === "proposed",
    kind: "implementation",
    execution_mode: "AFK",
    title: bounded("DEMO title 999"),
    objective: bounded("DEMO objective 999"),
    prompt: bounded("DEMO prompt preview 999", { truncated: true, full_href: "/api/task-breakdowns/demo/text/candidate-0-prompt" }),
    acceptance_criteria: bounded("DEMO acceptance 999"),
    proof: bounded("DEMO proof 999"),
    hitl_reason: bounded(""),
    constraints: bounded("DEMO constraint 999"),
    why_this_task_exists: bounded("Exists 999"),
    why_not_smaller: bounded("Not smaller 999"),
    why_not_larger: bounded("Not larger 999"),
    dependencies: bounded("Dependency 999"),
    likely_entry_points: bounded("src/demo.py"),
  };
  return {
    review: {
      id: "breakdown-demo-999", status, decision: "proposed_task_breakdown",
      model: bounded("DEMO-model-999"), session_id: "session-demo-999",
      session_href: "/sessions/session-demo-999", rationale: bounded("DEMO rationale 999"),
      source_text: bounded("DEMO source 2099", { truncated: true, full_href: "/api/task-breakdowns/demo/text/source" }),
      failure_type: status === "failed" ? bounded("provider_error") : null,
      failure_message: status === "failed" ? bounded("Safe DEMO failure 999") : null,
      created_task_ids: page(status === "accepted" ? [bounded("task-demo-999")] : []),
    },
    candidates: page(status === "failed" ? [] : [candidate]),
    context: {
      global_contract_summary: bounded("DEMO global contract 999"),
      global_constraints: page([bounded("DEMO global constraint 999")]),
      verification: page([bounded("Run DEMO verification 999")]),
      rejected_items: page([{ text: bounded("Rejected DEMO 999"), reason: bounded("Not a task") }]),
      non_goals: page([bounded("No real data")]),
      recommended_sequence: page([bounded("DEMO title 999")]),
    },
    repo_context: {
      available: true, source: bounded("repo_context_brief"), text_chars: 999,
      documents: page([bounded("AGENTS.md")]), manifests: page([bounded("pyproject.toml")]),
      entrypoints: page([bounded("src/demo.py")]), test_commands: page([bounded("uv run pytest")]),
      tracked_files_sample: page([bounded("tests/demo.py")]),
    },
    controls: {
      can_accept: status === "proposed", can_retry: status === "failed",
      can_create_manual_candidate: status === "failed",
    },
    links: {
      self_href: "/task-breakdowns/breakdown-demo-999/review",
      api_href: "/api/task-breakdowns/breakdown-demo-999/review",
      board_href: "/app/projects/project-demo-999/board",
      accept_href: status === "proposed" ? "/task-breakdowns/breakdown-demo-999/accept" : null,
      retry_href: status === "failed" ? "/task-breakdowns/breakdown-demo-999/retry" : null,
      manual_href: status === "failed" ? "/task-breakdowns/breakdown-demo-999/manual" : null,
    },
  };
}

function breakdownDraft(data, { overflow = false } = {}) {
  const fields = Object.fromEntries(Object.entries(data.candidates.items[0] || {})
    .filter(([, value]) => value && typeof value === "object" && "preview" in value)
    .map(([field, value]) => [field, {
      value: value.preview, loaded: !value.truncated, fullHref: value.full_href,
      touched: false, error: null,
    }]));
  return {
    candidates: data.candidates.items.length ? [{
      index: 0, selected: true, kind: "implementation", executionMode: "AFK",
      kindTouched: false, executionModeTouched: false, fields,
    }] : [],
    candidatePagination: { ...data.candidates.pagination, has_more: overflow, next_href: overflow ? "/api/task-breakdowns/demo/evidence/candidates?offset=1&limit=50" : null },
    globalContract: { value: "DEMO global contract 999", loaded: true, touched: false, error: null },
    globalConstraints: { value: "DEMO global constraint 999", loaded: true, touched: false, error: null },
    verification: { value: "Run DEMO verification 999", loaded: true, touched: false, error: null },
  };
}

function renderBreakdown(status, options = {}) {
  const data = breakdownReviewData(status);
  if (options.acceptanceClaim) {
    data.controls = {
      can_accept: false,
      can_retry: false,
      can_create_manual_candidate: false,
    };
    data.links.accept_href = null;
  }
  return renderToStaticMarkup(React.createElement(TaskBreakdownReviewState, {
    breakdownId: data.review.id,
    data,
    draft: breakdownDraft(data, options),
    loading: false,
    error: null,
    dirty: Boolean(options.dirty),
  }));
}

test("Task Breakdown Review renders proposed parity and bounded edit gates", () => {
  const markup = renderBreakdown("proposed", { dirty: true });
  for (const text of [
    "Task Breakdown Review", "DEMO title 999", "Candidate kind", "Execution mode",
    "Acceptance criteria", "Candidate proof / verification path", "Task slicing evidence",
    "Global contract summary", "Rejected as Tasks", "Repo Context Brief",
    "Accept selected and estimate", "Unsaved browser-local edits",
  ]) assert.match(markup, new RegExp(text));
  assert.match(markup, /Load full text before editing/);
  assert.match(markup, /disabled=""/);
});

test("Task Breakdown Review renders failed recovery, accepted evidence, and overflow gate", () => {
  const failed = renderBreakdown("failed");
  assert.match(failed, /Breakdown failed/);
  assert.match(failed, /Retry breakdown/);
  assert.match(failed, /Create manual candidate/);
  assert.match(failed, /Safe DEMO failure 999/);
  assert.match(failed, /Preserved context/);
  assert.match(failed, /Repo Context Brief/);

  const accepted = renderBreakdown("accepted");
  assert.match(accepted, /Accepted review/);
  assert.match(accepted, /task-demo-999/);
  assert.match(accepted, /Accepted candidates/);
  assert.match(accepted, /DEMO title 999/);
  assert.match(accepted, /Global contract summary/);
  assert.match(accepted, /Repo Context Brief/);
  assert.doesNotMatch(accepted, /Accept selected and estimate/);

  const overflow = renderBreakdown("proposed", { overflow: true });
  assert.match(overflow, /Load remaining candidates/);
  assert.match(overflow, /Load every candidate before acceptance/);
  assert.match(overflow, /Accept selected and estimate<\/button>/);
});

test("Task Breakdown Review renders a proposed acceptance claim read-only", () => {
  const markup = renderBreakdown("proposed", { acceptanceClaim: true });
  assert.match(markup, /Acceptance in progress/);
  assert.match(markup, /controlled operator repair/);
  assert.match(markup, /DEMO title 999/);
  assert.doesNotMatch(markup, /Accept selected and estimate|Candidate kind|Execution mode/);
});

function reviewButton(root, label) {
  return root.findAllByType("button").find((button) => button.children.join("").includes(label));
}

function mountedReview(breakdownId, setGuard = () => {}, navigate = () => true) {
  return React.createElement(
    NavContext.Provider,
    { value: navigate },
    React.createElement(
      NavigationGuardContext.Provider,
      { value: setGuard },
      React.createElement(TaskBreakdownReview, { breakdownId }),
    ),
  );
}

test("Task Breakdown controller pages, loads full text, and installs dirty guards", async (t) => {
  const originalFetch = globalThis.fetch;
  const originalWindow = globalThis.window;
  const originalActFlag = globalThis.IS_REACT_ACT_ENVIRONMENT;
  t.after(() => {
    globalThis.fetch = originalFetch;
    globalThis.window = originalWindow;
    globalThis.IS_REACT_ACT_ENVIRONMENT = originalActFlag;
  });
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  let guard = null;
  let beforeUnload = null;
  const data = breakdownReviewData("proposed");
  data.review.source_text = bounded("DEMO source 2099");
  data.candidates.pagination = {
    offset: 0, limit: 1, total: 2, has_more: true,
    next_href: "/api/task-breakdowns/demo/evidence/candidates?offset=1&limit=1",
  };
  const second = { ...data.candidates.items[0], index: 1, title: bounded("DEMO title 2") };
  globalThis.window = {
    location: { pathname: "/task-breakdowns/breakdown-demo-999/review", assign: () => {} },
    confirm: () => false,
    addEventListener: (name, listener) => { if (name === "beforeunload") beforeUnload = listener; },
    removeEventListener: () => {},
  };
  globalThis.fetch = async (url) => {
    if (url === data.links.api_href) return { ok: true, json: async () => data };
    if (String(url).includes("evidence/candidates")) {
      return { ok: true, json: async () => page([second]) };
    }
    if (String(url).includes("candidate-0-prompt")) {
      return { ok: true, text: async () => "Complete DEMO prompt 999" };
    }
    throw new Error(`Unexpected fetch: ${url}`);
  };

  let renderer;
  await act(async () => { renderer = create(mountedReview(data.review.id, (value) => { guard = value; })); });
  assert.equal(reviewButton(renderer.root, "Accept selected").props.disabled, true);
  await act(async () => { await reviewButton(renderer.root, "Load remaining candidates").props.onClick(); });
  assert.equal(reviewButton(renderer.root, "Accept selected").props.disabled, false);
  assert.equal(reviewButton(renderer.root, "Load remaining candidates"), undefined);
  await act(async () => { await reviewButton(renderer.root, "Load full text before editing").props.onClick(); });
  assert(renderer.root.findAllByType("textarea").some((field) => field.props.value === "Complete DEMO prompt 999"));

  const title = renderer.root.findAllByType("input").find((field) => field.props.value === "DEMO title 999");
  await act(async () => { title.props.onChange({ target: { value: "Edited DEMO title 999" } }); });
  assert.equal(typeof guard, "function");
  assert.equal(guard(), false);
  const event = { prevented: false, returnValue: null, preventDefault() { this.prevented = true; } };
  beforeUnload(event);
  assert.equal(event.prevented, true);
  assert.equal(event.returnValue, "");
  await act(async () => { renderer.unmount(); });
});

test("Task Breakdown Retry and Manual refetch authoritative same-state evidence", async (t) => {
  const originalFetch = globalThis.fetch;
  const originalWindow = globalThis.window;
  const originalActFlag = globalThis.IS_REACT_ACT_ENVIRONMENT;
  t.after(() => {
    globalThis.fetch = originalFetch;
    globalThis.window = originalWindow;
    globalThis.IS_REACT_ACT_ENVIRONMENT = originalActFlag;
  });
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  const first = breakdownReviewData("failed");
  const second = breakdownReviewData("failed");
  const recovered = breakdownReviewData("proposed");
  first.review.source_text = bounded("DEMO source 2099");
  second.review.source_text = bounded("DEMO source 2099");
  first.review.failure_message = bounded("Old failure preview", { truncated: true, full_href: "/api/task-breakdowns/demo/text/failure-message" });
  second.review.failure_message = bounded("New failure preview", { truncated: true, full_href: "/api/task-breakdowns/demo/text/failure-message" });
  first.context.non_goals = page([bounded("Old non-goal")]);
  second.context.non_goals = page([bounded("New non-goal")]);
  const reviewPayloads = [first, second, recovered];
  const posted = [];
  const postedBodies = [];
  globalThis.window = {
    location: { pathname: "/task-breakdowns/breakdown-demo-999/review", assign: () => {} },
    confirm: () => true,
    addEventListener: () => {},
    removeEventListener: () => {},
  };
  globalThis.fetch = async (url, options = {}) => {
    if (options.method === "POST") {
      posted.push(url);
      postedBodies.push(Object.fromEntries(options.body.entries()));
      return { ok: true, json: async () => ({ ok: true, next_href: first.links.self_href }) };
    }
    if (url === first.links.api_href) {
      return { ok: true, json: async () => reviewPayloads.shift() };
    }
    if (url === "/api/task-breakdowns/demo/text/failure-message") {
      return { ok: true, text: async () => "Old full failure" };
    }
    throw new Error(`Unexpected fetch: ${url}`);
  };

  let renderer;
  await act(async () => { renderer = create(mountedReview(first.review.id)); });
  const fullTextButtons = renderer.root.findAllByType("button").filter((button) => button.children.join("").includes("Load full text"));
  await act(async () => { await fullTextButtons.at(-1).props.onClick(); });
  assert.match(JSON.stringify(renderer.toJSON()), /Old full failure/);

  await act(async () => { await reviewButton(renderer.root, "Retry breakdown").props.onClick(); });
  const retried = JSON.stringify(renderer.toJSON());
  assert.match(retried, /New failure preview/);
  assert.match(retried, /New non-goal/);
  assert.doesNotMatch(retried, /Old full failure|Old non-goal/);

  await act(async () => { await reviewButton(renderer.root, "Create manual candidate").props.onClick(); });
  assert.match(JSON.stringify(renderer.toJSON()), /Accept selected and estimate/);
  assert.deepEqual(posted, [first.links.retry_href, first.links.manual_href]);
  assert.deepEqual(postedBodies, [{}, {}]);
  await act(async () => { renderer.unmount(); });
});

test("dirty Retry confirms, single-flights, and follows accepted replay navigation", async (t) => {
  const originalFetch = globalThis.fetch;
  const originalWindow = globalThis.window;
  const originalActFlag = globalThis.IS_REACT_ACT_ENVIRONMENT;
  t.after(() => {
    globalThis.fetch = originalFetch;
    globalThis.window = originalWindow;
    globalThis.IS_REACT_ACT_ENVIRONMENT = originalActFlag;
  });
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  const failed = breakdownReviewData("failed");
  failed.review.source_text = bounded("Complete DEMO source 2099");
  let allowRetry = false;
  let confirmations = 0;
  let postCount = 0;
  let resolvePost;
  const postResponse = new Promise((resolve) => { resolvePost = resolve; });
  const navigated = [];
  globalThis.window = {
    location: { pathname: failed.links.self_href, assign: (path) => navigated.push(path) },
    confirm: () => { confirmations += 1; return allowRetry; },
    addEventListener: () => {},
    removeEventListener: () => {},
  };
  globalThis.fetch = async (url, options = {}) => {
    if (options.method === "POST") {
      postCount += 1;
      return postResponse;
    }
    if (url === failed.links.api_href) return { ok: true, json: async () => failed };
    throw new Error(`Unexpected fetch: ${url}`);
  };

  let renderer;
  await act(async () => {
    renderer = create(mountedReview(failed.review.id, () => {}, (path) => navigated.push(path)));
  });
  const manualTitle = renderer.root.findAllByType("input").find((field) => field.props.value === "Manual task from source");
  await act(async () => { manualTitle.props.onChange({ target: { value: "Edited DEMO manual 999" } }); });
  await act(async () => { await reviewButton(renderer.root, "Retry breakdown").props.onClick(); });
  assert.equal(postCount, 0);

  allowRetry = true;
  let first;
  await act(async () => {
    first = reviewButton(renderer.root, "Retry breakdown").props.onClick();
    reviewButton(renderer.root, "Retry breakdown").props.onClick();
    resolvePost({
      ok: true,
      json: async () => ({ ok: true, status: "accepted", next_href: failed.links.board_href }),
    });
    await first;
  });
  assert.equal(postCount, 1);
  assert.equal(confirmations, 2);
  assert.deepEqual(navigated, [failed.links.board_href]);
  await act(async () => { renderer.unmount(); });
});

test("Task Breakdown action controller negotiates exact JSON and preserves safe failures", async () => {
  let request;
  const success = await submitBreakdownAction({
    url: "/task-breakdowns/demo/accept",
    body: new URLSearchParams({ accept_0: "1" }),
    fetchImpl: async (url, options) => {
      request = { url, options };
      return { ok: true, json: async () => ({ ok: true, next_href: "/app/projects/demo/board" }) };
    },
  });
  assert.equal(success.ok, true);
  assert.equal(request.options.method, "POST");
  assert.equal(request.options.headers.Accept, "application/json");
  assert.equal(request.options.credentials, "same-origin");

  const failure = await submitBreakdownAction({
    url: "/task-breakdowns/demo/retry",
    body: new URLSearchParams(),
    fetchImpl: async () => ({ ok: false, json: async () => ({
      ok: false, error: "Safe validation failure", retry_href: "/task-breakdowns/demo/review",
    }) }),
  });
  assert.deepEqual(failure, {
    ok: false, error: "Safe validation failure", retryHref: "/task-breakdowns/demo/review",
  });
});

test("Task Breakdown Accept omits loaded-only redacted values and submits actual edits", () => {
  const data = breakdownReviewData("proposed");
  const draft = breakdownDraft(data);
  draft.candidates[0].fields.prompt = {
    value: "complete [REDACTED] prompt 999", loaded: true, touched: false, fullHref: null, error: null,
  };
  const loadOnly = buildAcceptForm(draft);
  assert.equal(loadOnly.get("accept_0"), "1");
  assert.equal(loadOnly.has("prompt_0"), false);

  draft.candidates[0].fields.prompt.touched = true;
  draft.candidates[0].fields.prompt.value = "operator-edited [REDACTED] prompt 999";
  const edited = buildAcceptForm(draft);
  assert.equal(edited.get("prompt_0"), "operator-edited [REDACTED] prompt 999");
});

test("Task Breakdown Review distinguishes loading, safe error, and empty states", () => {
  const loading = renderToStaticMarkup(React.createElement(TaskBreakdownReviewState, {
    breakdownId: "breakdown-demo-999", data: null, draft: null, loading: true, error: null,
  }));
  assert.match(loading, /Loading Task Breakdown Review/);

  const failedLoad = renderToStaticMarkup(React.createElement(TaskBreakdownReviewState, {
    breakdownId: "breakdown-demo-999", data: null, draft: null, loading: false, error: new Error("secret detail"),
  }));
  assert.match(failedLoad, /Could not load Task Breakdown Review/);
  assert.match(failedLoad, /Retry review/);
  assert.doesNotMatch(failedLoad, /secret detail|server-rendered/);

  const empty = renderToStaticMarkup(React.createElement(TaskBreakdownReviewState, {
    breakdownId: "breakdown-demo-999", data: null, draft: null, loading: false, error: null,
  }));
  assert.match(empty, /No Task Breakdown Review state available/);
});

test("Task Breakdown Review is exact-route owned without swallowing suffixes", () => {
  assert.deepEqual(parseRoute("/task-breakdowns/breakdown-demo-999/review"), {
    view: "taskBreakdownReview", breakdownId: "breakdown-demo-999",
  });
  assert.equal(parseRoute("/task-breakdowns/breakdown-demo-999/review/extra").view, "notFound");
  assert.equal(parseRoute("/app/task-breakdowns/breakdown-demo-999/review").view, "notFound");
});
