import React from "react";

import { NavContext } from "./nav.jsx";
import Shell from "./components/Shell.jsx";
import Dashboard from "./views/Dashboard.jsx";
import Workspace from "./views/Workspace.jsx";
import Board from "./views/Board.jsx";

// The shell is served under /app. Client routes mirror the Jinja URLs so the
// two surfaces stay legible during migration:
//   /app                      -> React dashboard
//   /app/projects/:id         -> React project workspace
//   /app/projects/:id/board   -> React project board shell
export function parseRoute(pathname) {
  const normalized = pathname.replace(/\/$/, "");
  if (normalized === "/app") return { view: "dashboard" };

  const board = normalized.match(/^\/app\/projects\/([^/]+)\/board$/);
  if (board) return { view: "board", projectId: board[1] };

  const workspace = normalized.match(/^\/app\/projects\/([^/]+)$/);
  if (workspace) return { view: "workspace", projectId: workspace[1] };

  return { view: "notFound" };
}

export default function App() {
  // History API routing: pushState on in-shell links, popstate for back and
  // forward. Deep links to the three declared React routes still work because
  // FastAPI serves this same index for each route on a full load.
  const [path, setPath] = React.useState(window.location.pathname);
  const [navRefreshKey, setNavRefreshKey] = React.useState(0);

  React.useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate = React.useCallback((to) => {
    window.history.pushState(null, "", to);
    setPath(to);
  }, []);

  const route = parseRoute(path);
  const activeProjectId = route.projectId || null;
  let content;
  if (route.view === "workspace") {
    content = (
      <Workspace
        key={route.projectId}
        projectId={route.projectId}
        onProjectRestored={() => setNavRefreshKey((current) => current + 1)}
      />
    );
  } else if (route.view === "board") {
    content = <Board projectId={route.projectId} />;
  } else if (route.view === "dashboard") {
    content = <Dashboard />;
  } else {
    content = (
      <div className="notice danger">
        This React Portal route does not exist. <a href="/app">Open dashboard</a>.
      </div>
    );
  }
  return (
    <NavContext.Provider value={navigate}>
      <Shell
        activeView={route.view}
        activeProjectId={activeProjectId}
        refreshKey={navRefreshKey}
      >
        {content}
      </Shell>
    </NavContext.Provider>
  );
}