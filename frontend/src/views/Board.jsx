import React, { useEffect, useMemo, useState } from "react";

import { AppLink, NavContext } from "../nav.jsx";
import { getJSON } from "../api.js";

const COLUMNS = ["Estimated", "Running", "Review", "Done", "Blocked"];

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

export default function Board({ projectId }) {
  const navigate = React.useContext(NavContext);
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState(null);

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

  return <BoardState
    projectId={projectId}
    data={state.data}
    error={state.error}
    loading={state.loading}
    query={query}
    setQuery={setQuery}
    notice={notice}
    action={action}
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
    <div className="toolbar">
      <span className={`pill ${queueRunning ? "running" : "idle"}`}>Queue {data.automation.queue.status}</span>
      <span className="column-count">{data.board_summary.total_tasks} tasks · {data.automation.eligible_count} eligible</span>
      <button className="btn small" onClick={() => action(`/projects/${projectId}/run-next`)}>Run next</button>
      {queueRunning ? <button className="btn small secondary" onClick={() => action(`/projects/${projectId}/queue/stop`)}>Stop queue</button> : <QueueStart projectId={projectId} queue={data.automation.queue} action={action} />}
      {data.board_summary.counts.Done > 0 && <button className="btn small secondary" onClick={() => action(`/projects/${projectId}/tasks/archive-done`)}>Archive all Done</button>}
      <AppLink className="btn small secondary" to={`/projects/${projectId}`}>Workspace</AppLink>
      <AppLink className="btn small secondary" to={data.history_href}>History</AppLink>
      <a className="btn small secondary" href={`/projects/${projectId}/board`}>Server board</a>
    </div>
    <section className="panel">
      <label htmlFor="react-board-intake">Short task intake</label>
      <form className="board-intake" onSubmit={(event) => { event.preventDefault(); action(`/projects/${projectId}/tasks/estimate-form`, new FormData(event.currentTarget)); }}>
        <textarea className="board-input" id="react-board-intake" name="description" placeholder="Describe a short task or paste Markdown" rows="3" />
        <input className="board-file" name="markdown_file" type="file" accept=".md,text/markdown,text/plain" />
        <button className="btn small" type="submit">Estimate task</button>
      </form>
      <p className="muted">Markdown paste or upload opens authoritative Task Breakdown Review.</p>
    </section>
    <div className="toolbar"><input className="board-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter loaded tasks" /><span className="column-count">{cards.filter(visible).length} of {cards.length} visible</span></div>
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
  return <form className="toolbar" onSubmit={(event) => {
    event.preventDefault();
    action(`/projects/${projectId}/queue/start`, new FormData(event.currentTarget));
  }}>
    <label className="check-row"><input name="auto_agent_review" type="checkbox" defaultChecked={queue.auto_agent_review} /> Auto Agent Review</label>
    <button className="btn small secondary" type="submit">Start queue</button>
  </form>;
}

function TaskCard({ task, projectId, adapters, action }) {
  const { controls, details } = task;
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
    <p className="task-title">{task.summary.text || task.id}</p>
    <div className="task-meta"><span>{task.id}</span>{task.estimate_tokens != null && <span>Estimate: {task.estimate_tokens.toLocaleString()}</span>}{task.actual_tokens != null && <span>Actual: {task.actual_tokens.toLocaleString()}</span>}{task.launch_model && <span>Run: {task.launch_model}</span>}{task.launch_model && task.recommended_model && task.launch_model !== task.recommended_model && <span>Recommended: {task.recommended_model}</span>}</div>
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
  return <details>
    <summary>Details</summary>
    {task.session_href && <p><a href={task.session_href}>Session report</a></p>}
    <TextEvidence label="Task body" value={details.task_body} />
    {details.token_components.available && <section><h4>Worker token components</h4><ul>{details.token_components.items.map((item) => <li key={item.key}>{item.label}: {item.value}</li>)}</ul>{details.token_components.turn_count != null && <p>Turns: {details.token_components.turn_count}</p>}{details.token_components.cost != null && <p>Cost: {details.token_components.cost}</p>}</section>}
    <section><h4>Launch</h4><dl className="detail-grid">{Object.entries(details.launch).filter(([, value]) => value != null && typeof value !== "object").map(([key, value]) => <React.Fragment key={key}><dt>{key}</dt><dd>{String(value)}</dd></React.Fragment>)}</dl><TextEvidence label="Launch error" value={details.launch.error} /><TextEvidence label="Blocked reason" value={details.launch.blocked_reason} /><TextEvidence label="Retryable failure" value={details.launch.retryable_failure.summary} /><TextEvidence label="Diagnostic" value={details.launch.diagnostic.summary} /><TextEvidence label="Next action" value={details.launch.diagnostic.next_action} /></section>
    {details.timeline.length > 0 && <section><h4>Timeline</h4><ul>{details.timeline.map((event, index) => <li key={`${event.created_at}-${index}`}><span className="muted">{event.created_at} · {event.kind}</span><br /><strong>{event.title || event.kind}</strong> · {event.detail_summary.text}</li>)}</ul></section>}
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
