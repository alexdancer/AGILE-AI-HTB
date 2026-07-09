import React from "react";

import Shell from "./components/Shell.jsx";
import Workspace from "./views/Workspace.jsx";
import Board from "./views/Board.jsx";

// The shell is served under /app. Client routes mirror the Jinja URLs so the
// two surfaces stay legible during migration:
//   /app/projects/:id        -> React project workspace
//   /app/projects/:id/board  -> React project board shell
export function parseRoute(pathname) {
  const parts = pathname
    .replace(/^\/app\/?/, "")
    .split("/")
    .filter(Boolean);
  if (parts[0] === "projects" && parts[1]) {
    if (parts[2] === "board") {
      return { view: "board", projectId: parts[1] };
    }
    return { view: "workspace", projectId: parts[1] };
  }
  return { view: "home" };
}

function Home() {
  return (
    <Shell>
      <h1 className="page-title">React Portal shell</h1>
      <p className="page-sub">
        This is the first migrated Portal surface. Open a project workspace or
        board to use it.
      </p>
      <div className="panel">
        <div className="panel-body">
          <p className="muted">
            Pick a connected project from the{" "}
            <a href="/projects">projects list</a>, then open its React workspace
            at <code>/app/projects/&lt;id&gt;</code> or its board at{" "}
            <code>/app/projects/&lt;id&gt;/board</code>.
          </p>
        </div>
      </div>
    </Shell>
  );
}

export default function App() {
  const route = parseRoute(window.location.pathname);
  if (route.view === "workspace") {
    return <Workspace projectId={route.projectId} />;
  }
  if (route.view === "board") {
    return <Board projectId={route.projectId} />;
  }
  return <Home />;
}
