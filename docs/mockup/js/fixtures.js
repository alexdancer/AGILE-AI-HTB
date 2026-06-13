/* AGILE-AI-HTB — fixture data for the front-end mockup.
 *
 * All values are obviously synthetic:
 *   - session IDs prefixed DEMO_SESSION_2099_*
 *   - timestamps in year 2099
 *   - token counts rounded to obviously-fake values
 *   - account/owner labels prefixed DEMO
 *
 * Shapes mirror the real FastAPI responses (see
 * src/token_tracker_harness/routes/*.py and alarms.py/estimation.py)
 * so the mockup can later be wired to the live API with a one-line
 * fetch swap. Do not delete the AGILE-AI-HTBDemoFakeDataInvariantTests
 * test that guards this invariant.
 */

window.AGILE_AI_HTB = window.AGILE_AI_HTB || {};

window.AGILE_AI_HTB.fixtures = {
  meta: {
    portal: "AGILE-AI-HTB",
    generated_at: "2099-06-13T09:00:00Z",
    project: "Fired-Fest 24h Challenge — Token Tracker Harness",
    daily_cap_tokens: 1_000_000,
    daily_used_tokens: 612_400,
  },

  // ---- Sessions (matches /session/{id}/report shape) ------------------
  sessions: [
    {
      session: {
        id: "DEMO_SESSION_2099_a1f3",
        task_description: "Refactor auth module to use dependency-injected validators",
        model: "gpt-4o-mini",
        status: "active",
        started_at: "2099-06-13T08:14:11Z",
        guardrail_overrides: {
          budget: { daily_used_tokens: 612_400, daily_cap_tokens: 1_000_000 },
        },
      },
      task_metadata: {
        description: "Refactor auth module to use dependency-injected validators",
        model: "gpt-4o-mini",
        status: "active",
      },
      token_totals: { prompt_tokens: 188_220, completion_tokens: 71_980, total_tokens: 260_200 },
      current_zone: "yellow",
      alarms: [
        "DEMO_ALARM_2099_001",
        "DEMO_ALARM_2099_004",
      ],
      checkpoints: [
        { name: "budget_zone",  status: "warn",  detail: "zone=yellow, 61% of daily cap" },
        { name: "loop_check",   status: "ok",    detail: "no repeating tool pattern" },
        { name: "session_cap",  status: "ok",    detail: "32% of session cap" },
      ],
      tool_breakdown: {
        "file.read":   { calls: 47 },
        "file.write":  { calls: 12 },
        "shell.run":   { calls: 18 },
        "tests.run":   { calls: 6  },
      },
    },
    {
      session: {
        id: "DEMO_SESSION_2099_b204",
        task_description: "Add CSV export endpoint with streaming response",
        model: "gpt-4o",
        status: "active",
        started_at: "2099-06-13T07:42:09Z",
        guardrail_overrides: { budget: { daily_used_tokens: 612_400, daily_cap_tokens: 1_000_000 } },
      },
      task_metadata: {
        description: "Add CSV export endpoint with streaming response",
        model: "gpt-4o",
        status: "active",
      },
      token_totals: { prompt_tokens: 92_100, completion_tokens: 41_300, total_tokens: 133_400 },
      current_zone: "green",
      alarms: [],
      checkpoints: [
        { name: "budget_zone",  status: "ok",    detail: "zone=green, 13% of daily cap" },
        { name: "loop_check",   status: "ok",    detail: "no repeating tool pattern" },
        { name: "session_cap",  status: "ok",    detail: "22% of session cap" },
      ],
      tool_breakdown: {
        "file.read":   { calls: 14 },
        "file.write":  { calls: 4  },
        "shell.run":   { calls: 5  },
      },
    },
    {
      session: {
        id: "DEMO_SESSION_2099_c881",
        task_description: "Investigate flaky integration test in payments/charge.py",
        model: "claude-sonnet-4",
        status: "paused",
        started_at: "2099-06-13T06:55:21Z",
        guardrail_overrides: { budget: { daily_used_tokens: 612_400, daily_cap_tokens: 1_000_000 } },
      },
      task_metadata: {
        description: "Investigate flaky integration test in payments/charge.py",
        model: "claude-sonnet-4",
        status: "paused",
      },
      token_totals: { prompt_tokens: 51_700, completion_tokens: 28_900, total_tokens: 80_600 },
      current_zone: "red",
      alarms: [
        "DEMO_ALARM_2099_002",
        "DEMO_ALARM_2099_003",
      ],
      checkpoints: [
        { name: "budget_zone",  status: "fail",  detail: "zone=red, 89% of session cap" },
        { name: "loop_check",   status: "warn",  detail: "tests.run called 14x in 3 min" },
      ],
      tool_breakdown: {
        "file.read":   { calls: 31 },
        "tests.run":   { calls: 14 },
        "shell.run":   { calls: 9  },
      },
    },
    {
      session: {
        id: "DEMO_SESSION_2099_d009",
        task_description: "Generate OpenAPI client SDK for internal customers",
        model: "gpt-4o-mini",
        status: "completed",
        started_at: "2099-06-13T04:11:50Z",
        guardrail_overrides: { budget: { daily_used_tokens: 612_400, daily_cap_tokens: 1_000_000 } },
      },
      task_metadata: {
        description: "Generate OpenAPI client SDK for internal customers",
        model: "gpt-4o-mini",
        status: "completed",
      },
      token_totals: { prompt_tokens: 73_400, completion_tokens: 64_800, total_tokens: 138_200 },
      current_zone: "green",
      alarms: [],
      checkpoints: [
        { name: "budget_zone", status: "ok", detail: "zone=green" },
        { name: "loop_check",  status: "ok", detail: "clean" },
      ],
      tool_breakdown: {
        "file.read":  { calls: 22 },
        "file.write": { calls: 19 },
      },
    },
  ],

  // ---- Alarms (matches Alarm.as_dict shape) ---------------------------
  alarms: [
    {
      id: "DEMO_ALARM_2099_001",
      type: "budget_zone_yellow",
      severity: "warning",
      session_id: "DEMO_SESSION_2099_a1f3",
      timestamp: "2099-06-13T08:51:33Z",
      resolved: false,
      context: { daily_used_tokens: 612_400, daily_cap_tokens: 1_000_000, threshold: 0.60 },
      recommended_action: "Downgrade tool access and tighten max_tokens clamp",
    },
    {
      id: "DEMO_ALARM_2099_002",
      type: "session_cap_warning",
      severity: "critical",
      session_id: "DEMO_SESSION_2099_c881",
      timestamp: "2099-06-13T08:33:02Z",
      resolved: false,
      context: { session_used_tokens: 80_600, session_cap_tokens: 90_000, percent: 0.895 },
      recommended_action: "Pause session; ask human whether to raise cap, abort, or adjust guardrails",
    },
    {
      id: "DEMO_ALARM_2099_003",
      type: "loop_detected",
      severity: "warning",
      session_id: "DEMO_SESSION_2099_c881",
      timestamp: "2099-06-13T08:21:47Z",
      resolved: false,
      context: { tool: "tests.run", repeated_calls: 14, window_seconds: 180 },
      recommended_action: "Break loop: vary input or escalate to human",
    },
    {
      id: "DEMO_ALARM_2099_004",
      type: "tool_category_limit",
      severity: "info",
      session_id: "DEMO_SESSION_2099_a1f3",
      timestamp: "2099-06-13T08:18:09Z",
      resolved: false,
      context: { category: "shell", weight: 0.82, limit: 0.80 },
      recommended_action: "Restrict shell access for the remainder of this session",
    },
    {
      id: "DEMO_ALARM_2099_005",
      type: "budget_zone_red",
      severity: "critical",
      session_id: "DEMO_SESSION_2099_e510",
      timestamp: "2099-06-13T07:02:18Z",
      resolved: true,
      resolved_action: "raise_budget",
      context: { daily_used_tokens: 980_000, daily_cap_tokens: 1_000_000 },
      recommended_action: "Daily cap imminent — escalate to human for budget decision",
    },
  ],

  // ---- Tasks (matches /tasks + /estimate shapes) -----------------------
  tasks: [
    { id: "DEMO_TASK_2099_t01", description: "Add CSV export endpoint", status: "In Progress", estimate_tokens: 25_000, recommended_model: "gpt-4o-mini", actual_tokens: 13_400 },
    { id: "DEMO_TASK_2099_t02", description: "Refactor auth module", status: "In Progress", estimate_tokens: 100_000, recommended_model: "gpt-4o-mini", actual_tokens: 260_200 },
    { id: "DEMO_TASK_2099_t03", description: "Investigate flaky test", status: "Blocked", estimate_tokens: 50_000, recommended_model: "claude-sonnet-4", actual_tokens: 80_600 },
    { id: "DEMO_TASK_2099_t04", description: "Generate SDK from OpenAPI", status: "Done", estimate_tokens: 75_000, recommended_model: "gpt-4o-mini", actual_tokens: 138_200 },
    { id: "DEMO_TASK_2099_t05", description: "Add rate-limit middleware", status: "Backlog", estimate_tokens: 25_000, recommended_model: "gpt-4o-mini" },
  ],

  // ---- Estimate sample (matches EstimateResult.as_dict) ----------------
  estimateSamples: [
    { description: "fix typo in README", token_estimate: 5_000,  complexity: "simple",  recommended_model: "gpt-4o-mini",    budget_note: null },
    { description: "add a new REST endpoint with tests", token_estimate: 25_000, complexity: "modest", recommended_model: "gpt-4o-mini", budget_note: null },
    { description: "refactor auth module to use dependency injection", token_estimate: 100_000, complexity: "complex", recommended_model: "gpt-4o",     budget_note: "Budget low — recommended model clamped from gpt-4o to gpt-4o-mini" },
  ],

  // ---- Live proxy request trace (matches streaming events) -------------
  proxyTrace: [
    { ts: "08:51:32.114", tag: "req",     text: "POST /v1/chat/completions  model=gpt-4o-mini  stream=true" },
    { ts: "08:51:32.118", tag: "gov",     text: "zone=yellow  apply(prompt_rewrite, max_tokens=4096, blocked=[shell.reboot])" },
    { ts: "08:51:32.121", tag: "openai",  text: "→ upstream openai  stream=open  usage=true" },
    { ts: "08:51:33.402", tag: "chunk",   text: "data: {\"choices\":[{\"delta\":{\"content\":\"Sure, I'll start by reading \"}}]}" },
    { ts: "08:51:33.812", tag: "chunk",   text: "data: {\"choices\":[{\"delta\":{\"content\":\"the auth module and \"}}]}" },
    { ts: "08:51:34.501", tag: "chunk",   text: "data: {\"choices\":[{\"delta\":{\"content\":\"its tests...\"}}]}" },
    { ts: "08:51:41.220", tag: "tool",    text: "→ tool.file.read  path=src/auth/validators.py" },
    { ts: "08:51:42.018", tag: "tool",    text: "← tool.file.read  1402 bytes" },
    { ts: "08:51:51.300", tag: "warn",    text: "budget_alarm trigger threshold=0.60  zone=yellow" },
    { ts: "08:51:51.302", tag: "alarm",   text: "DEMO_ALARM_2099_001 budget_zone_yellow  persist=ok" },
    { ts: "08:51:55.110", tag: "chunk",   text: "data: {\"choices\":[{\"delta\":{\"content\":\"I see — the validators \"}}]}" },
    { ts: "08:52:01.880", tag: "chunk",   text: "data: [DONE]  usage={prompt:1840, completion:612, total:2452}" },
  ],
};
