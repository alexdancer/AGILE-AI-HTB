import React from "react";

import Shell from "../components/Shell.jsx";
import { useResource } from "../useResource.js";

const COLUMN_ORDER = ["Estimated", "Running", "Review", "Done", "Blocked"];

export default function Workspace({ projectId }) {
  const { data, error, loading } = useResource(
    `/api/projects/${projectId}/workspace`,
  );

  if (loading) {
    return (
      <Shell>
        <p className="spinner">Loading project workspace…</p>
      </Shell>
    );
  }
  if (error) {
    return (
      <Shell>
        <div className="notice danger">
          Could not load project workspace: {error.message}
        </div>
        <p>
          <a href={`/projects/${projectId}`}>Open the server-rendered workspace</a>
        </p>
      </Shell>
    );
  }

  const { project, summary } = data;
  const counts = summary.counts || {};

  return (
    <Shell>
      <h1 className="page-title">{project.name}</h1>
      <p className="page-sub">
        {project.root_path} · capability: {summary.capability_state}
      </p>

      {summary.launch_ready ? (
        <div className="notice">Worker launch is ready for this project.</div>
      ) : (
        <div className="notice warning">
          No launchable Worker adapter is ready yet.
        </div>
      )}

      <div className="kpi-row">
        {COLUMN_ORDER.map((column) => (
          <div className="kpi" key={column}>
            <div className="label">{column}</div>
            <div className="value">{counts[column] ?? 0}</div>
          </div>
        ))}
      </div>

      <div className="toolbar">
        <a className="btn" href={`/app/projects/${projectId}/board`}>
          Open board
        </a>
        <a
          className="btn secondary"
          href={`/projects/${projectId}/task-history`}
        >
          Task history
        </a>
      </div>

      {summary.attention_actions && summary.attention_actions.length > 0 && (
        <div className="panel">
          <div className="panel-header">
            <h3>Needs attention</h3>
          </div>
          <div className="panel-body">
            {summary.attention_actions.map((action, index) => (
              <div className={`notice ${toneClass(action.tone)}`} key={index}>
                <a href={action.href}>{action.label}</a> — {action.detail}
              </div>
            ))}
          </div>
        </div>
      )}
    </Shell>
  );
}

function toneClass(tone) {
  if (tone === "yellow") return "warning";
  if (tone === "red") return "danger";
  return "";
}
