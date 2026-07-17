import React, { useCallback, useState } from "react";

import { getJSON, postJSON } from "../api.js";
import { AppLink } from "../nav.jsx";
import { useResource } from "../useResource.js";

const safeError = (error) =>
  error?.status === 401
    ? "Projects require sign-in."
    : "Could not load projects. Retry.";

function boundedError(value, fallback) {
  return typeof value === "string" && value ? value.slice(0, 1000) : fallback;
}

export default function Projects() {
  const [refreshKey, setRefreshKey] = useState(0);
  const { data, error, loading } = useResource("/api/projects", refreshKey);
  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  return (
    <ProjectsState
      data={data}
      error={error}
      loading={loading}
      onRefresh={refresh}
    />
  );
}

export function ProjectsState({ data, error, loading, onRefresh }) {
  const [rootPath, setRootPath] = useState("");
  const [status, setStatus] = useState(null);
  const [inlineError, setInlineError] = useState(null);
  const [activeAction, setActiveAction] = useState(null);
  const busy = activeAction !== null;
  const isBusy = (projectId, kind) =>
    activeAction?.projectId === projectId && activeAction?.kind === kind;

  const clearMessages = () => {
    setStatus(null);
    setInlineError(null);
  };

  const connect = async (event) => {
    event.preventDefault();
    if (!rootPath.trim()) return;
    clearMessages();
    setActiveAction({ projectId: null, kind: "connect" });
    try {
      const outcome = await postJSON("/settings/project/connect", {
        root_path: rootPath.trim(),
      });
      if (outcome?.project) {
        setStatus("Project connected.");
        setRootPath("");
        onRefresh();
      } else {
        setInlineError("Could not connect project.");
      }
    } catch (err) {
      setInlineError(boundedError(err.message, "Could not connect project."));
    } finally {
      setActiveAction(null);
    }
  };

  const archive = async (projectId) => {
    clearMessages();
    setActiveAction({ projectId, kind: "archive" });
    try {
      const outcome = await postJSON(`/projects/${projectId}/archive`, {});
      if (outcome?.ok) {
        setStatus("Project archived.");
        onRefresh();
      } else {
        setInlineError(boundedError(outcome?.error, "Could not archive project."));
      }
    } catch (err) {
      setInlineError(boundedError(err.message, "Could not archive project."));
    } finally {
      setActiveAction(null);
    }
  };

  const restore = async (projectId) => {
    clearMessages();
    setActiveAction({ projectId, kind: "restore" });
    try {
      const outcome = await postJSON(`/projects/${projectId}/restore`, {});
      if (outcome?.ok) {
        setStatus("Project restored.");
        onRefresh();
      } else {
        setInlineError(boundedError(outcome?.error, "Could not restore project."));
      }
    } catch (err) {
      setInlineError(boundedError(err.message, "Could not restore project."));
    } finally {
      setActiveAction(null);
    }
  };

  if (loading && !data) {
    return <p className="spinner">Loading projects…</p>;
  }
  if (error) {
    return (
      <>
        <div className="notice danger">{safeError(error)}</div>
        <p>
          <a href="/projects">Retry</a>
        </p>
      </>
    );
  }

  const localRunnerEnabled = data?.local_runner_enabled ?? false;
  const activeProjects = data?.projects || [];
  const archivedProjects = data?.archived_projects || [];

  return (
    <>
      <h1 className="page-title">Projects</h1>
      <p className="page-sub">open local repo · enter project workspace</p>

      <div className="live-notice" aria-live="polite">
        {inlineError ? (
          <p className="notice danger">{inlineError}</p>
        ) : status ? (
          <p className="notice">{status}</p>
        ) : null}
      </div>

      <section className="panel">
        <div className="panel-header"><h3>Open local repo</h3></div>
        <div className="panel-body">
          {!localRunnerEnabled && (
            <>
              <span className="pill yellow">Local Runner disabled</span>
              <p className="muted mono">
                Run <code>foremanctl init</code>, enable Local Runner in{" "}
                <code>.foreman/config.toml</code> or with{" "}
                <code>foremanctl serve --local-runner</code>, then add the
                control-plane key in <code>/settings/control-plane</code> if
                needed.
              </p>
            </>
          )}
          <form onSubmit={connect}>
            <label htmlFor="root-path">Local repository path</label>
            <input
              id="root-path"
              value={rootPath}
              onChange={(e) => setRootPath(e.target.value)}
              placeholder="/path/to/local/repo"
              required
              disabled={busy}
            />
            <button
              type="submit"
              className="primary"
              style={{ marginTop: 10 }}
              disabled={busy}
            >
              {isBusy(null, "connect") ? "Connecting…" : "Open project"}
            </button>
          </form>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header"><h3>Active projects</h3></div>
        <div className="panel-body">
          {activeProjects.length === 0 ? (
            <p className="muted">No projects yet.</p>
          ) : (
            <div className="dashboard-grid">
              {activeProjects.map((project) => (
                <article className="card" key={project.id}>
                  <CapabilityPill state={project.capability?.state} label={project.capability?.label} />
                  <h2 className="mono" style={{ fontSize: 16, margin: "10px 0 6px" }}>
                    <AppLink to={`/projects/${project.id}`}>{project.name}</AppLink>
                  </h2>
                  <p className="muted mono" style={{ margin: 0 }}>
                    {project.root_path}
                  </p>
                  {project.capability?.reasons?.length > 0 && (
                    <ul className="mono muted" style={{ margin: "8px 0 0", fontSize: 12 }}>
                      {project.capability.reasons.map((reason, i) => (
                        <li key={i}>{reason}</li>
                      ))}
                    </ul>
                  )}
                  <button
                    type="button"
                    onClick={() => archive(project.id)}
                    disabled={busy}
                    style={{ marginTop: 12 }}
                  >
                    {isBusy(project.id, "archive") ? "Archiving…" : "Archive project"}
                  </button>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header"><h3>Archived projects</h3></div>
        <div className="panel-body">
          {archivedProjects.length === 0 ? (
            <p className="muted">No archived projects.</p>
          ) : (
            <div className="dashboard-grid">
              {archivedProjects.map((project) => (
                <article className="card" key={project.id}>
                  <span className="pill muted">archived</span>
                  <h2 className="mono" style={{ fontSize: 16, margin: "10px 0 6px" }}>
                    <AppLink to={`/projects/${project.id}`}>{project.name}</AppLink>
                  </h2>
                  <p className="muted mono" style={{ margin: 0 }}>
                    {project.root_path}
                  </p>
                  <p className="muted mono" style={{ margin: "8px 0 0", fontSize: 12 }}>
                    Archived {project.archived_at}
                  </p>
                  <button
                    type="button"
                    className="primary"
                    onClick={() => restore(project.id)}
                    disabled={busy}
                    style={{ marginTop: 12 }}
                  >
                    {isBusy(project.id, "restore") ? "Restoring…" : "Restore project"}
                  </button>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}

function CapabilityPill({ state, label }) {
  if (state === "launch_ready") return <span className="pill green">{label || "Launch-ready"}</span>;
  if (state === "analysis_ready") return <span className="pill blue">{label || "Analysis-ready"}</span>;
  return <span className="pill red">{label || "Blocked"}</span>;
}
