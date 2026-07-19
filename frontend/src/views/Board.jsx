import React, { useEffect, useMemo, useState } from "react";

import { AppLink, NavContext } from "../nav.jsx";
import { getJSON } from "../api.js";
import { drainLiveEvents, runSingleFlight } from "../live-events.js";

const COLUMNS = ["Estimated", "Running", "Review", "Done", "Blocked"];
const TASK_NAME_WORD_LIMIT = 7;

export function taskDisplayName(task) {
  const source = String(task?.name || task?.title || task?.summary?.text || task?.id || "Untitled task").trim();
  const lines = source.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const heading = lines.find((line) => /^#{1,6}\s+/.test(line));
  let candidate = (heading || lines[0] || source)
    .replace(/^#{1,6}\s+/, "")
    .replace(/^[-*+]\s+(?:\[[ xX]\]\s*)?/, "")
    .replace(/^\d+[.)]\s+/, "")
    .replace(/[*_`]/g, "")
    .replace(/^(?:task|title|summary)\s*:\s*/i, "")
    .replace(/^please\s+/i, "")
    .replace(/^(?:can|could|would)\s+you\s+/i, "")
    .replace(/^(?:i\s+(?:kind of\s+)?want(?:ed)?\s+to|we\s+need\s+to)\s+/i, "")
    .replace(/\s+/g, " ")
    .trim();

  candidate = candidate.split(/[.!?;]\s+/)[0].replace(/[.!?;:]$/, "").trim();
  for (const separator of [" so that ", " and then ", " while ", " but ", " and "]) {
    const index = candidate.toLowerCase().indexOf(separator);
    if (index > 0 && candidate.slice(0, index).trim().split(/\s+/).length >= 3) {
      candidate = candidate.slice(0, index).trim();
      break;
    }
  }

  let words = candidate.split(/\s+/).filter(Boolean).slice(0, TASK_NAME_WORD_LIMIT);
  while (words.length > 1 && /^(?:a|an|and|for|of|or|the|to|with)$/i.test(words.at(-1))) words = words.slice(0, -1);
  const compact = words.join(" ") || task?.id || "Untitled task";
  return compact.charAt(0).toUpperCase() + compact.slice(1);
}

const safeError = (error) =>
  error?.status === 401
    ? "Board requires sign-in."
    : "Could not load board. Retry.";

export async function submitBoardAction({ url, body, fetchImpl, navigate, reload, onNotice }) {
  onNotice(null);
  try {
    const response = await fetchImpl(url, {
      method: "POST",
      body,
      headers: { Accept: "application/json" },
      credentials: "same-origin",
    });
    const outcome = await response.json();
    if (outcome.next_href) {
      navigate(outcome.next_href);
      return "navigated";
    }
    if (!response.ok || !outcome.ok) {
      onNotice({ message: outcome.error || "Board action failed.", setupHref: outcome.setup_href });
      await reload();
      return "failed";
    }
    await reload();
    return "reloaded";
  } catch (error) {
    onNotice({ message: error.message || "Board action failed.", setupHref: null });
    return "error";
  }
}

export function mergeBoardStatus(current, status) {
  if (!current.data) return current;
  return {
    ...current,
    data: {
      ...current.data,
      automation: {
        ...current.data.automation,
        counts: status.counts,
        queue: status.queue,
        live_refresh_enabled: status.has_active_runs || status.queue_active,
      },
    },
  };
}

export async function pollBoardStatus({ getStatus, reload, update }) {
  try {
    const status = await getStatus();
    if (status.reload_required) {
      await reload();
      return "reloaded";
    }
    update((current) => mergeBoardStatus(current, status));
    return "merged";
  } catch {
    return "retained";
  }
}

export function mergeBoardLiveEvents(current, sessionId, events) {
  if (!current.data || !events.length) return current;
  let changed = false;
  const tasksByStatus = Object.fromEntries(Object.entries(current.data.tasks_by_status).map(([status, tasks]) => [status, tasks.map((task) => {
    if (task.status !== "Running" || task.session_href !== `/sessions/${sessionId}`) return task;
    const timeline = task.details.timeline || [];
    const known = new Set(timeline.map((event) => event.id).filter((id) => Number.isInteger(id)));
    const appended = events.filter((event) => Number.isInteger(event.id) && !known.has(event.id)).map((event) => ({
      ...event,
      detail_summary: { text: event.detail_summary || "", truncated: false },
    }));
    if (!appended.length) return task;
    changed = true;
    return { ...task, details: { ...task.details, timeline: [...timeline, ...appended].slice(-50) } };
  })]));
  return changed ? { ...current, data: { ...current.data, tasks_by_status: tasksByStatus } } : current;
}

export default function Board({ projectId }) {
  const navigate = React.useContext(NavContext);
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState(null);
  const [estimating, setEstimating] = useState(false);
  const eventCursors = React.useRef(new Map());
  const eventPollInFlight = React.useRef(false);
  const runningSessionKey = useMemo(() => (state.data?.tasks_by_status.Running || [])
    .map((task) => task.session_href || "")
    .filter(Boolean)
    .sort()
    .join(","), [state.data?.tasks_by_status.Running]);

  const load = async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const data = await getJSON(`/api/projects/${projectId}/board`);
      setState({ data, error: null, loading: false });
    } catch (error) {
      setState({ data: null, error, loading: false });
    }
  };

  useEffect(() => { load(); }, [projectId]);
  useEffect(() => {
    if (!state.data?.automation?.live_refresh_enabled) return undefined;
    const timer = window.setInterval(async () => {
      await pollBoardStatus({
        getStatus: () => getJSON(`/projects/${projectId}/board/status`),
        reload: load,
        update: setState,
      });
    }, 2500);
    return () => window.clearInterval(timer);
  }, [projectId, state.data?.automation?.live_refresh_enabled]);
  useEffect(() => {
    if (!state.data?.automation?.live_refresh_enabled) return undefined;
    const running = state.data.tasks_by_status.Running || [];
    const sessionIds = running
      .map((task) => task.session_href?.replace(/^\/sessions\//, ""))
      .filter(Boolean);
    if (!sessionIds.length) return undefined;
    for (const task of running) {
      const sessionId = task.session_href?.replace(/^\/sessions\//, "");
      if (!sessionId || eventCursors.current.has(sessionId)) continue;
      const ids = (task.details.timeline || []).map((event) => event.id).filter(Number.isInteger);
      eventCursors.current.set(sessionId, ids.length ? Math.max(...ids) : null);
    }
    let stopped = false;
    const poll = () => runSingleFlight(eventPollInFlight, async () => {
      for (const sessionId of sessionIds) {
        const sinceId = eventCursors.current.get(sessionId);
        try {
          const next = await drainLiveEvents({
            sessionId,
            sinceId,
            getEvents: getJSON,
            stopped: () => stopped,
            append: (events) => setState((current) => mergeBoardLiveEvents(current, sessionId, events)),
          });
          if (stopped) return;
          if (Number.isInteger(next)) eventCursors.current.set(sessionId, next);
        } catch {
          // Board status polling remains authoritative if the lightweight feed is unavailable.
        }
      }
    });
    poll();
    const timer = window.setInterval(poll, 5000);
    return () => { stopped = true; window.clearInterval(timer); };
  }, [state.data?.automation?.live_refresh_enabled, projectId, runningSessionKey]);

  const action = async (url, body = new FormData()) => {
    await submitBoardAction({
      url,
      body,
      fetchImpl: fetch,
      navigate: (href) => {
        if (/^\/task-breakdowns\/[^/]+\/review$/.test(href)) navigate(href);
        else window.location.assign(href);
      },
      reload: load,
      onNotice: setNotice,
    });
  };

  const estimateTask = async (body) => {
    setEstimating(true);
    try {
      await action(`/projects/${projectId}/tasks/estimate-form`, body);
    } finally {
      setEstimating(false);
    }
  };

  return <BoardState
    projectId={projectId}
    data={state.data}
    error={state.error}
    loading={state.loading}
    query={query}
    setQuery={setQuery}
    notice={notice}
    action={action}
    estimateTask={estimateTask}
    estimating={estimating}
  />;
}

export function BoardState({
  projectId,
  data,
  error,
  loading,
  query = "",
  setQuery = () => {},
  notice = null,
  action = () => {},
  estimateTask = () => {},
  estimating = false,
}) {
  if (loading) return <p className="spinner">Loading board…</p>;
  if (isArchivedBoardError(error)) return <>
    <div className="notice warning">
      <strong>Archived project</strong>
      <p className="muted">Restore this project before opening its active board.</p>
    </div>
    <p><AppLink to={`/projects/${projectId}`}>Open workspace to Restore</AppLink></p>
  </>;
  if (error) return <><div className="notice danger">{safeError(error)}</div></>;
  if (!data) return <div className="empty-state">No board state available.</div>;

  const cards = Object.values(data.tasks_by_status).flat();
  const visible = (task) => JSON.stringify(task).toLowerCase().includes(query.toLowerCase());
  const queueRunning = data.automation.queue.status === "running";

  return <>
    <h1 className="page-title">{data.project.name} · Board</h1>
    <p className="page-sub">Governed project task loop. FastAPI owns lifecycle and guardrails.</p>
    {notice && <div className="notice danger">{notice.message}{notice.setupHref && <> · <a href={notice.setupHref}>Open setup</a></>}</div>}
    <div className="board-command-bar">
      <div className="board-command-status">
        <span className={`pill ${queueRunning ? "running" : "idle"}`}>Queue {data.automation.queue.status}</span>
        <span className="column-count">{data.board_summary.total_tasks} tasks · {data.automation.eligible_count} eligible</span>
      </div>
      <div className="board-command-actions">
        <button className="btn small" onClick={() => action(`/projects/${projectId}/run-next`)}>Run next</button>
        {queueRunning ? <button className="btn small secondary" onClick={() => action(`/projects/${projectId}/queue/stop`)}>Stop queue</button> : <QueueStart projectId={projectId} queue={data.automation.queue} action={action} />}
        {data.board_summary.counts.Done > 0 && <button className="btn small secondary" onClick={() => action(`/projects/${projectId}/tasks/archive-done`)}>Archive all Done</button>}
        <AppLink className="btn small secondary" to={`/projects/${projectId}`}>Workspace</AppLink>
        <AppLink className="btn small secondary" to={data.history_href}>History</AppLink>
        <a className="btn small secondary" href={`/projects/${projectId}/board`}>Server board</a>
      </div>
    </div>
    <section className="panel board-intake-panel" aria-busy={estimating}>
      <div className="panel-header"><h3>Short task intake</h3></div>
      <div className="panel-body">
        <form className="board-intake" onSubmit={(event) => { event.preventDefault(); if (estimating) return; estimateTask(new FormData(event.currentTarget)); }}>
          <label className="board-intake-task-field" htmlFor="react-board-intake">
            <span>Task description</span>
            <textarea className="board-input" id="react-board-intake" name="description" placeholder="Describe a short task or paste Markdown" rows="3" disabled={estimating} />
          </label>
          <label className="board-intake-file-field">
            <span>Markdown file <em>(optional)</em></span>
            <input className="board-file" name="markdown_file" type="file" accept=".md,text/markdown,text/plain" disabled={estimating} />
          </label>
          <button className="btn small" type="submit" disabled={estimating}>{estimating ? "Estimating…" : "Estimate task"}</button>
          {estimating && <div className="board-intake-progress" role="status" aria-live="polite">
            <div className="board-intake-progress-copy">
              <strong>Preparing Task Breakdown Review</strong>
              <span>Estimating and breaking down the task. Keep this page open.</span>
            </div>
            <div className="board-intake-progress-track" role="progressbar" aria-label="Task estimation progress" aria-valuetext="Estimating task and preparing review">
              <span className="board-intake-progress-bar" />
            </div>
          </div>}
        </form>
        <p className="board-intake-hint muted">Markdown paste or upload opens authoritative Task Breakdown Review.</p>
      </div>
    </section>
    <div className="board-filter-toolbar"><input className="board-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter loaded tasks" /><span className="column-count">{cards.filter(visible).length} of {cards.length} visible</span></div>
    <div className="board">
      {COLUMNS.map((column) => <section className="column" key={column}><div className="panel-header"><h3>{column}</h3><span className="column-count">{data.tasks_by_status[column].filter(visible).length}</span></div>{data.tasks_by_status[column].filter(visible).map((task) => <TaskCard key={task.id} task={task} projectId={projectId} adapters={data.adapters} action={action} />)}{data.tasks_by_status[column].filter(visible).length === 0 && <div className="empty-state">{query ? "No matching tasks" : data.board_empty_states[column]}</div>}</section>)}
    </div>
  </>;
}

function isArchivedBoardError(error) {
  return error?.status === 409 && String(error.message || "").includes("restore archived project");
}

function boundedError(value, fallback) {
  return typeof value === "string" && value ? value.slice(0, 1000) : fallback;
}

function QueueStart({ projectId, queue, action }) {
  return <form className="board-queue-start" onSubmit={(event) => {
    event.preventDefault();
    action(`/projects/${projectId}/queue/start`, new FormData(event.currentTarget));
  }}>
    <label className="check-row"><input name="auto_agent_review" type="checkbox" defaultChecked={queue.auto_agent_review} /> Auto Agent Review</label>
    <button className="btn small secondary" type="submit">Start queue</button>
  </form>;
}

function TaskCard({ task, projectId, adapters, action }) {
  const { controls, details } = task;
  const fullSummary = task.summary.text || task.id;
  const displayName = taskDisplayName(task);
  const defaultAdapter = adapters.find((adapter) => adapter.is_default) || adapters[0];
  const [adapterId, setAdapterId] = useState(defaultAdapter?.id || "");
  const selectedAdapter = adapters.find((adapter) => adapter.id === adapterId) || defaultAdapter;
  const initialModel = selectedAdapter?.allowed_models.includes(task.recommended_model)
    ? task.recommended_model
    : selectedAdapter?.allowed_models[0] || "";
  const [model, setModel] = useState(initialModel);
  const [budgetOverride, setBudgetOverride] = useState(false);
  const [nativeAcknowledged, setNativeAcknowledged] = useState(false);
  const [reviewPrompt, setReviewPrompt] = useState(details.review.prompt.text);
  const [blockedReason, setBlockedReason] = useState("");

  const launch = () => {
    const form = new FormData();
    form.set("project_id", projectId);
    if (adapterId) form.set("adapter_id", adapterId);
    if (model) form.set("model", model);
    if (budgetOverride) form.set("budget_override", "on");
    if (nativeAcknowledged) form.set("native_budget_acknowledged", "on");
    action(`/tasks/${task.id}/launch`, form);
  };
  const review = (actionName, extra = {}) => {
    action(`/tasks/${task.id}/review`, reviewForm(projectId, actionName, extra));
  };

  return <article className="task">
    <header className="task-heading">
      <span className="task-id">{task.id}</span>
      <h4 className="task-title" title={fullSummary}>{displayName}</h4>
    </header>
    <div className="task-meta">{task.estimate_tokens != null && <span>Estimate {task.estimate_tokens.toLocaleString()}</span>}{task.actual_tokens != null && <span>Actual {task.actual_tokens.toLocaleString()}</span>}{task.launch_model && <span>Run {task.launch_model}</span>}{task.launch_model && task.recommended_model && task.launch_model !== task.recommended_model && <span>Recommended {task.recommended_model}</span>}</div>
    {controls.can_launch && <div className="card-controls">
      <label>Worker Adapter<select className="board-input" value={adapterId} onChange={(event) => {
        const nextId = event.target.value;
        const nextAdapter = adapters.find((adapter) => adapter.id === nextId);
        setAdapterId(nextId);
        setModel(nextAdapter?.allowed_models.includes(task.recommended_model) ? task.recommended_model : nextAdapter?.allowed_models[0] || "");
      }}>{adapters.map((adapter) => <option key={adapter.id} value={adapter.id}>{adapter.name}{adapter.is_default ? " · Default" : ""}</option>)}</select></label>
      <label>Worker model<select className="board-input" value={model} onChange={(event) => setModel(event.target.value)}>{(selectedAdapter?.allowed_models || []).map((modelId) => <option key={modelId} value={modelId}>{modelId}</option>)}</select></label>
      {controls.budget_override_available && <label className="check-row"><input type="checkbox" checked={budgetOverride} onChange={(event) => setBudgetOverride(event.target.checked)} /> Approve budget override</label>}
      {controls.native_usage_override_ack_required && <label className="check-row"><input type="checkbox" checked={nativeAcknowledged} onChange={(event) => setNativeAcknowledged(event.target.checked)} /> {controls.native_usage_override_ack_text}</label>}
      <button className="btn small" type="button" onClick={launch}>Launch</button>
      {!selectedAdapter?.launchable && controls.setup_href && <a href={controls.setup_href}>Open Worker Setup</a>}
    </div>}
    {controls.can_refresh && <button className="btn small" type="button" onClick={() => action(`/tasks/${task.id}/refresh`, reviewForm(projectId))}>Refresh</button>}
    {controls.can_archive && <button className="btn small secondary" onClick={() => action(`/projects/${projectId}/tasks/${task.id}/archive`)}>Archive</button>}
    {controls.can_dismiss && <button className="btn small secondary" onClick={() => action(`/projects/${projectId}/tasks/${task.id}/archive`)}>Dismiss</button>}
    {(controls.can_save_review_prompt || controls.can_agent_review || controls.can_mark_done || controls.can_block) && <div className="card-controls">
      <label>Review prompt<textarea className="board-input" rows="2" value={reviewPrompt} onChange={(event) => setReviewPrompt(event.target.value)} /></label>
      <div className="toolbar">
        {controls.can_save_review_prompt && <button className="btn small secondary" type="button" onClick={() => review("save_prompt", { review_prompt: reviewPrompt })}>Save review prompt</button>}
        {controls.can_agent_review && <button className="btn small secondary" type="button" onClick={() => review("agent_review", { review_prompt: reviewPrompt })}>Agent Review</button>}
        {controls.can_mark_done && <button className="btn small" type="button" onClick={() => review("mark_done")}>Mark Done</button>}
      </div>
      {controls.can_block && <div className="toolbar"><input className="board-input" value={blockedReason} onChange={(event) => setBlockedReason(event.target.value)} placeholder="Reason required to block" /><button className="btn small danger" type="button" onClick={() => review("block", { blocked_reason: blockedReason })}>Block</button></div>}
    </div>}
    <TaskDetails task={task} />
  </article>;
}

function TaskDetails({ task }) {
  const { details } = task;
  const review = details.review.agent_review;
  return <details className="task-details">
    <summary>Task details</summary>
    {task.session_href && <p><a href={task.session_href}>Session report</a></p>}
    <TextEvidence label="Task body" value={details.task_body} />
    {details.token_components.available && <section><h4>Worker token components</h4><ul>{details.token_components.items.map((item) => <li key={item.key}>{item.label}: {item.value}</li>)}</ul>{details.token_components.turn_count != null && <p>Turns: {details.token_components.turn_count}</p>}{details.token_components.cost != null && <p>Cost: {details.token_components.cost}</p>}</section>}
    <section><h4>Launch</h4><dl className="detail-grid">{Object.entries(details.launch).filter(([, value]) => value != null && typeof value !== "object").map(([key, value]) => <React.Fragment key={key}><dt>{key}</dt><dd>{String(value)}</dd></React.Fragment>)}</dl><TextEvidence label="Launch error" value={details.launch.error} /><TextEvidence label="Blocked reason" value={details.launch.blocked_reason} /><TextEvidence label="Retryable failure" value={details.launch.retryable_failure.summary} /><TextEvidence label="Diagnostic" value={details.launch.diagnostic.summary} /><TextEvidence label="Next action" value={details.launch.diagnostic.next_action} /></section>
    {details.timeline.length > 0 && <section><h4>Timeline</h4><ul>{details.timeline.map((event, index) => <li key={event.id ?? `${event.created_at}-${index}`}><span className="muted">{event.created_at} · {event.layer || "worker_harness"} · {event.kind}</span><br /><strong>{event.title || event.kind}</strong> · {event.detail_summary.text}{event.kind === "token" && <em> · Provisional usage; final total recorded on completion.</em>}</li>)}</ul></section>}
    <TextEvidence label="Worker stdout" value={details.logs.stdout} />
    <TextEvidence label="Worker stderr" value={details.logs.stderr} />
    <TextEvidence label="Saved review prompt" value={details.review.prompt} />
    <dl className="detail-grid">
      {review.status != null && <><dt>Review status</dt><dd>{review.status}</dd></>}
      {review.recommendation != null && <><dt>Recommendation</dt><dd>{review.recommendation}</dd></>}
      {review.model != null && <><dt>Review model</dt><dd>{review.model}</dd></>}
      {review.token_total != null && <><dt>Review tokens</dt><dd>{review.token_total}</dd></>}
    </dl>
    <TextEvidence label="Agent Review" value={review.summary} />
    <TextEvidence label="Agent Review failure" value={review.failure} />
    {review.findings.length > 0 && <section><h4>Review findings</h4><ul>{review.findings.map((finding, index) => <li key={`${finding.path || "finding"}-${index}`}><strong>{finding.severity || "finding"}</strong>: {finding.message.text}{finding.path && <> · {finding.path}{finding.line != null ? `:${finding.line}` : ""}</>}</li>)}</ul></section>}
    {review.review_session_href && <p><a href={review.review_session_href}>Agent Review session</a></p>}
    <TextEvidence label="Blocked" value={details.blocked.reason} />
    {details.blocked.requires_manual_estimate && <p className="notice warning">Manual estimate required</p>}
  </details>;
}

function TextEvidence({ label, value }) {
  if (!value?.text) return null;
  return <section><h4>{label}</h4><pre className="raw-evidence">{value.text}</pre>{value.truncated && <p className="muted">Truncated for board display.</p>}</section>;
}

function reviewForm(projectId, actionName, values = {}) {
  const form = new FormData();
  form.set("project_id", projectId);
  if (actionName) form.set("action", actionName);
  for (const [key, value] of Object.entries(values)) form.set(key, value);
  return form;
}
