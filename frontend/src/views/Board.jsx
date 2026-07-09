import React from "react";

import Shell from "../components/Shell.jsx";
import { useResource } from "../useResource.js";

export default function Board({ projectId }) {
  const { data, error, loading } = useResource(
    `/api/projects/${projectId}/board`,
  );

  if (loading) {
    return (
      <Shell>
        <p className="spinner">Loading board…</p>
      </Shell>
    );
  }
  if (error) {
    return (
      <Shell>
        <div className="notice danger">
          Could not load board: {error.message}
        </div>
        <p>
          <a href={`/projects/${projectId}/board`}>
            Open the server-rendered board
          </a>
        </p>
      </Shell>
    );
  }

  const {
    project,
    columns = [],
    tasks_by_status: tasksByStatus = {},
    board_empty_states: emptyStates = {},
    automation_summary: automation,
  } = data;

  const queueRunning = automation && automation.queue
    ? automation.queue.status === "running"
    : false;

  return (
    <Shell>
      <h1 className="page-title">{project.name} · Board</h1>
      <p className="page-sub">
        Project-scoped task board. Launch, queue, and review actions run through
        the governed FastAPI flow.
      </p>

      <div className="toolbar">
        <span className={`pill ${queueRunning ? "running" : "idle"}`}>
          Queue {queueRunning ? "running" : "idle"}
        </span>
        {automation && (
          <span className="column-count">
            {automation.eligible_count} eligible · {automation.counts.Running}{" "}
            running
          </span>
        )}
        {/* Actions post to existing FastAPI routes; guardrails stay backend-side. */}
        <form method="post" action={`/projects/${projectId}/run-next`}>
          <button className="btn small" type="submit">
            Run next
          </button>
        </form>
        {queueRunning ? (
          <form method="post" action={`/projects/${projectId}/queue/stop`}>
            <button className="btn small secondary" type="submit">
              Stop queue
            </button>
          </form>
        ) : (
          <form method="post" action={`/projects/${projectId}/queue/start`}>
            <button className="btn small" type="submit">
              Start queue
            </button>
          </form>
        )}
        <a className="btn small secondary" href={`/projects/${projectId}/board`}>
          Full board (launch / review)
        </a>
      </div>

      <div className="board">
        {columns.map((column) => {
          const tasks = tasksByStatus[column] || [];
          return (
            <section className="column" key={column}>
              <div className="panel-header">
                <h3>{column}</h3>
                <span className="column-count">{tasks.length}</span>
              </div>
              {tasks.length === 0 ? (
                <div className="empty-state">
                  {emptyStates[column] || `No ${column} tasks.`}
                </div>
              ) : (
                tasks.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    projectId={projectId}
                  />
                ))
              )}
            </section>
          );
        })}
      </div>
    </Shell>
  );
}

function TaskCard({ task, projectId }) {
  const tokens =
    task.actual_tokens != null
      ? `${task.actual_tokens.toLocaleString()} tok`
      : task.estimated_tokens != null
        ? `~${task.estimated_tokens.toLocaleString()} tok`
        : null;
  return (
    <article className="task">
      <p className="task-title">{task.title || task.id}</p>
      <div className="task-meta">
        <span>{task.id}</span>
        {tokens && <span>{tokens}</span>}
        {task.status === "Review" && (
          <a href={`/projects/${projectId}/board`}>Review →</a>
        )}
      </div>
    </article>
  );
}
