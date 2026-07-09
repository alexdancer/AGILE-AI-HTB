import React from "react";

import { AppLink } from "../nav.jsx";
import { useResource } from "../useResource.js";

// Home is the React shell's project picker: operators who open `/app` reach
// every migrated surface by clicking, never by typing a URL.
// The Shell (sidebar + chrome) is provided by App.jsx, so this view renders
// only the main content region.
export default function Home() {
  const { data, error, loading } = useResource("/api/projects");

  if (loading) {
    return <p className="spinner">Loading connected projects…</p>;
  }
  if (error) {
    return (
      <>
        <div className="notice danger">
          Could not load connected projects: {error.message}
        </div>
        <p>
          <a href="/projects">Open the server-rendered projects page</a>
        </p>
      </>
    );
  }

  const projects = data.projects || [];

  return (
    <>
      <h1 className="page-title">Projects</h1>
      <p className="page-sub">
        Pick a connected project to open its workspace or board.
      </p>

      {projects.length === 0 ? (
        <div className="panel">
          <div className="panel-body">
            <div className="empty-state">
              No projects are connected yet. Connect a repository to start
              estimating and launching Worker slices.
            </div>
            {/* The connect-project flow stays server-rendered; full navigation. */}
            <p>
              <a className="btn" href="/settings/project">
                Connect a project
              </a>
            </p>
          </div>
        </div>
      ) : (
        projects.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))
      )}
    </>
  );
}

function ProjectCard({ project }) {
  const counts = project.counts || {};
  const capability = (project.capability || {}).state || "unknown";
  return (
    <div className="panel">
      <div className="panel-header">
        <h3>
          <AppLink to={`/app/projects/${project.id}`}>{project.name}</AppLink>
        </h3>
        <span className="column-count">
          {project.total_tasks} tasks · {capability}
        </span>
      </div>
      <div className="panel-body">
        <p className="muted">{project.root_path}</p>
        <div className="toolbar">
          <AppLink className="btn" to={`/app/projects/${project.id}`}>
            Open workspace
          </AppLink>
          <AppLink
            className="btn secondary"
            to={`/app/projects/${project.id}/board`}
          >
            Open board
          </AppLink>
          {counts.Review > 0 && (
            <span className="pill running">{counts.Review} in review</span>
          )}
        </div>
      </div>
    </div>
  );
}