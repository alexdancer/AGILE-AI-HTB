import React from "react";

import { AppLink } from "../nav.jsx";
import { useResource } from "../useResource.js";

// Shell renders the same application frame as the Jinja `base.html` Portal:
// top brand bar, left sidebar (project list + Setup/Governance/Planning/
// Settings groups + logout), main content, footer. Sidebar nav data comes
// from the authenticated `/api/portal/nav` endpoint which reuses the same
// `portal_template_context` helper the Jinja sidebar uses, so both shells
// draw from a single source of truth.
//
// React-owned routes (/app, /app/projects/:id, /app/projects/:id/board) use
// AppLink for client-side navigation. Non-migrated Jinja pages use ordinary
// full-page anchors so the browser loads the server-rendered page.
//
// Props:
//   activeView: "dashboard" | "workspace" | "board"
//   activeProjectId: string | null
export default function Shell({ children, activeView, activeProjectId, refreshKey = 0 }) {
  const { data, error, loading } = useResource("/api/portal/nav", refreshKey);

  return (
    <div className="shell">
      <header className="topbar">
        <AppLink className="brand" to="/app">
          Foreman AI HQ<span className="dot">·</span>
          <span className="brand-portal">Portal</span>
        </AppLink>
      </header>
      <Sidebar
        activeView={activeView}
        activeProjectId={activeProjectId}
        data={data}
        error={error}
        loading={loading}
      />
      <main className="main">{children}</main>
      <footer className="shell-footer">
        Foreman AI HQ portal · operator-controlled budget governance
      </footer>
    </div>
  );
}

export function Sidebar({ activeView, activeProjectId, data, error, loading }) {
  const portalAuthRequired = data ? data.portal_auth_required : false;
  const projects = data ? data.sidebar_projects : [];
  const hasLoadedProjects = !loading && !error;

  return (
    <aside className="sidebar">
        <div className="group">Projects</div>
        <div className="project-list">
          {loading && <span className="sidebar-empty">Loading…</span>}
          {error && (
            <>
              <span className="sidebar-empty">Could not load projects.</span>
              <a className="sidebar-action" href="/login">Sign in again</a>
            </>
          )}
          {hasLoadedProjects && projects.length === 0 && (
            <span className="sidebar-empty">No projects</span>
          )}
          {hasLoadedProjects && projects.map((project) => {
            const isActive = activeProjectId === project.id;
            const hasTasks = project.task_count > 0;
            return (
              <React.Fragment key={project.id}>
                <AppLink
                  to={`/app/projects/${project.id}`}
                  className={`project-item${isActive ? " active" : ""}`}
                >
                  <span className="project-name">{project.name}</span>
                  <span className="project-sub">
                    {hasTasks ? "Task board" : "No tasks"}
                  </span>
                </AppLink>
                {hasTasks && (
                  <AppLink
                    to={`/app/projects/${project.id}/board`}
                    className={`project-board${isActive && activeView === "board" ? " active" : ""}`}
                  >
                    └ Task board
                  </AppLink>
                )}
              </React.Fragment>
            );
          })}
          <a href="/projects" className="sidebar-action">
            + Open local repo
          </a>
        </div>

        <div className="group">Setup</div>
        <nav>
          <a href="/setup">First-run setup</a>
        </nav>

        <div className="group">Governance</div>
        <nav>
          <AppLink
            to="/app"
            className={activeView === "dashboard" ? "active" : ""}
          >
            Dashboard
          </AppLink>
          <AppLink to="/sessions" className={activeView === "sessions" || activeView === "sessionReport" ? "active" : ""}>Sessions</AppLink>
          <AppLink to="/alarms" className={activeView === "alarms" ? "active" : ""}>Alarms</AppLink>
        </nav>

        {hasLoadedProjects && projects.length === 0 && (
          <>
            <div className="group">Planning</div>
            <nav>
              <a href="/board">Task board</a>
            </nav>
          </>
        )}

        <div className="group">Settings</div>
        <nav>
          <a href="/settings/control-plane" className={activeView === "controlPlaneSettings" ? "active" : ""}>Control plane model</a>
          <a href="/settings/budget" className={activeView === "budgetSettings" ? "active" : ""}>Token budget</a>
          <a href="/settings/project" className={activeView === "projectSettings" ? "active" : ""}>Projects</a>
          <a href="/settings/workers" className={activeView === "workerSettings" ? "active" : ""}>Worker adapters</a>
        </nav>

        {portalAuthRequired && (
          <form className="logout" action="/logout" method="post">
            <button type="submit">Logout</button>
          </form>
        )}
    </aside>
  );
}