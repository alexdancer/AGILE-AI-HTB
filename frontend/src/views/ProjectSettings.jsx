import React, { useCallback, useEffect, useState } from "react";

import { postJSON } from "../api.js";
import { useResource } from "../useResource.js";

const safeError = (error) =>
  error?.status === 401
    ? "Project settings require sign-in."
    : "Could not load project settings. Retry.";

// HTML callers (the canonical /projects list) are redirected here as
// /settings/project?error=<block reason>. Forward it to the API so the backend
// sanitizes and bounds it, matching what the server-rendered fallback page would
// render.
function initialErrorParam() {
  return new URLSearchParams(window.location.search).get("error") || null;
}

function clearUrlError() {
  const params = new URLSearchParams(window.location.search);
  if (!params.has("error")) return;
  params.delete("error");
  const query = params.toString();
  window.history.replaceState(null, "", `${window.location.pathname}${query ? "?" + query : ""}`);
}

export default function ProjectSettings() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [errorParam, setErrorParam] = useState(initialErrorParam);
  const url = errorParam
    ? `/api/settings/project?error=${encodeURIComponent(errorParam)}`
    : "/api/settings/project";
  const { data, error, loading } = useResource(url, refreshKey);
  const refresh = useCallback(() => {
    // A redirect-borne error describes the state before this action.
    clearUrlError();
    setErrorParam(null);
    setRefreshKey((k) => k + 1);
  }, []);

  return (
    <ProjectSettingsState
      data={data}
      error={error}
      loading={loading}
      onRefresh={refresh}
    />
  );
}

export function ProjectSettingsState({ data, error, loading, onRefresh }) {
  const [rootPath, setRootPath] = useState("");
  const [status, setStatus] = useState(null);
  const [inlineError, setInlineError] = useState(null);
  const [proofResult, setProofResult] = useState(null);
  // Which action is in flight, so only that button shows its busy label.
  const [activeAction, setActiveAction] = useState(null);
  const busy = activeAction !== null;
  const isBusy = (projectId, kind) =>
    activeAction?.projectId === projectId && activeAction?.kind === kind;

  useEffect(() => {
    if (data?.error) {
      setInlineError(data.error);
    }
  }, [data?.error]);

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
      const outcome = await postJSON("/settings/project/connect", { root_path: rootPath.trim() });
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

  const runReadOnlyProof = async (projectId) => {
    clearMessages();
    setProofResult(null);
    setActiveAction({ projectId, kind: "proof" });
    try {
      const res = await fetch(`/settings/project/${projectId}/read-only-proof`, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({}),
      });
      const outcome = await res.json();
      if (res.ok) {
        setProofResult({ projectId, outcome, passed: true });
        setStatus("Read-only proof launched.");
        onRefresh();
      } else if (res.status === 409 && outcome?.launch_guardrails) {
        setProofResult({ projectId, outcome, passed: false });
        setInlineError(
          boundedError(
            outcome.launch_guardrails.reasons?.join(" "),
            "Read-only proof blocked.",
          )
        );
      } else {
        const detail = outcome?.detail || outcome?.error || "Read-only proof failed.";
        throw new Error(detail);
      }
    } catch (err) {
      setInlineError(boundedError(err.message, "Could not launch read-only proof."));
    } finally {
      setActiveAction(null);
    }
  };

  if (loading && !data) {
    return <p className="spinner">Loading project settings…</p>;
  }
  if (error) {
    return (
      <>
        <div className="notice danger">{safeError(error)}</div>
        <p><a href="/settings/project">Retry</a></p>
      </>
    );
  }

  const localRunnerEnabled = data?.local_runner_enabled ?? false;
  const backendStatus = data?.backend_status || null;
  const connectedProjects = data?.connected_projects || [];
  const archivedProjects = data?.archived_projects || [];

  return (
    <>
      <h1 className="page-title">Projects</h1>
      <p className="page-sub">connect local repo · detect project profile · show local runner capability</p>

      {/* Wrapper stays mounted so aria-live announces whatever replaces it. */}
      <div className="live-notice" aria-live="polite">
        {inlineError ? (
          <p className="notice danger">{inlineError}</p>
        ) : status ? (
          <p className="notice">{status}</p>
        ) : null}
      </div>

      <section className="panel">
        <div className="panel-header"><h3>Local Runner</h3></div>
        <div className="panel-body">
          {localRunnerEnabled ? (
            <>
              <span className={`pill ${backendStatus?.online ? "green" : "yellow"}`}>enabled</span>
              {backendStatus?.online && <span className="pill green">online</span>}
              {backendStatus?.name && <span className="pill muted">{backendStatus.name}</span>}
            </>
          ) : (
            <>
              <span className="pill yellow">disabled</span>
              <p className="muted mono">
                Run <code>foremanctl init</code>, enable Local Runner in{" "}
                <code>.foreman/config.toml</code> or with{" "}
                <code>foremanctl serve --local-runner</code>, then add the control-plane key in{" "}
                <code>/settings/control-plane</code> if needed.
              </p>
            </>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header"><h3>Open local repo</h3></div>
        <div className="panel-body">
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
            <button type="submit" className="primary" style={{ marginTop: 10 }} disabled={busy}>
              {isBusy(null, "connect") ? "Connecting…" : "Open project"}
            </button>
          </form>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header"><h3>Active Project Profile</h3></div>
        <div className="panel-body">
          {connectedProjects.length === 0 ? (
            <p className="muted">No active projects.</p>
          ) : (
            connectedProjects.map((project) => (
              <article className="card" key={project.id}>
                <div className="flex" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                  <h2 className="mono" style={{ fontSize: 16, margin: "0 0 10px" }}>
                    {project.name}
                  </h2>
                  <CapabilityPill state={project.capability?.state} />
                </div>
                <dl className="workspace-kv">
                  <ProfileRow label="Root" value={project.root_path} />
                </dl>
                {project.capability?.reasons?.length > 0 && (
                  <>
                    <h3
                      className="mono"
                      style={{ fontSize: 12, textTransform: "uppercase", marginTop: 16, color: "var(--fg-2)" }}
                    >
                      Missing launch capability
                    </h3>
                    <ul className="mono muted">
                      {project.capability.reasons.map((reason, i) => (
                        <li key={i}>{reason}</li>
                      ))}
                    </ul>
                  </>
                )}
                {project.capability?.state === "launch_ready" && (
                  <button
                    type="button"
                    className="primary"
                    onClick={() => runReadOnlyProof(project.id)}
                    disabled={busy}
                    style={{ marginTop: 14 }}
                  >
                    {isBusy(project.id, "proof") ? "Running proof…" : "Run read-only proof"}
                  </button>
                )}
                {proofResult?.projectId === project.id && (
                  <ProofOutcome outcome={proofResult.outcome} passed={proofResult.passed} />
                )}
                <button
                  type="button"
                  onClick={() => archive(project.id)}
                  disabled={busy}
                  style={{ marginTop: 10 }}
                >
                  {isBusy(project.id, "archive") ? "Archiving…" : "Archive project"}
                </button>
              </article>
            ))
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header"><h3>Archived Projects</h3></div>
        <div className="panel-body">
          {archivedProjects.length === 0 ? (
            <p className="muted">No archived projects.</p>
          ) : (
            archivedProjects.map((project) => (
              <article className="card" key={project.id}>
                <div className="flex" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
                  <h2 className="mono" style={{ fontSize: 16, margin: "0 0 10px" }}>
                    {project.name}
                  </h2>
                  <span className="pill muted">archived</span>
                </div>
                <dl className="workspace-kv">
                  <ProfileRow label="Root" value={project.root_path} />
                </dl>
                <button
                  type="button"
                  className="primary"
                  onClick={() => restore(project.id)}
                  disabled={busy}
                  style={{ marginTop: 14 }}
                >
                  {isBusy(project.id, "restore") ? "Restoring…" : "Restore project"}
                </button>
              </article>
            ))
          )}
        </div>
      </section>
    </>
  );
}

function CapabilityPill({ state }) {
  if (state === "launch_ready") return <span className="pill green">Launch-ready via Local Runner</span>;
  if (state === "analysis_ready") return <span className="pill blue">Analysis-ready</span>;
  return <span className="pill red">Blocked</span>;
}

function ProofOutcome({ outcome, passed }) {
  const reasons = outcome?.launch_guardrails?.reasons;
  return (
    <p className={`notice ${passed ? "success" : "warning"}`}>
      {passed ? "Read-only proof launched" : "Read-only proof blocked"}
      {reasons?.length ? `: ${reasons.join(" ")}` : ""}
    </p>
  );
}

function ProfileRow({ label, value }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value || "not detected"}</dd>
    </>
  );
}

function boundedError(value, fallback) {
  return typeof value === "string" && value ? value.slice(0, 1000) : fallback;
}
