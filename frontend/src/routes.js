// Client routes mirror the canonical React-owned Portal URLs. The /app prefix
// is a permanent redirect alias supported by the server; the client also
// recognizes it so in-shell navigation from legacy bookmarks stays smooth.
export function parseRoute(pathname) {
  const normalized = pathname.replace(/\/$/, "");
  if (normalized === "/app") return { view: "dashboard" };
  if (normalized === "/dashboard") return { view: "dashboard" };
  if (normalized === "/projects") return { view: "projects" };
  if (normalized === "/setup") return { view: "setup" };
  if (normalized === "/alarms") return { view: "alarms" };
  if (normalized === "/sessions") return { view: "sessions" };
  if (normalized === "/settings/budget") return { view: "budgetSettings" };
  if (normalized === "/settings/control-plane") return { view: "controlPlaneSettings" };
  if (normalized === "/settings/project") return { view: "projectSettings" };
  if (normalized === "/settings/workers") return { view: "workerSettings" };

  const report = normalized.match(/^\/sessions\/([^/]+)$/);
  if (report) return { view: "sessionReport", sessionId: decodeURIComponent(report[1]) };

  const breakdownReview = normalized.match(/^\/task-breakdowns\/([^/]+)\/review$/);
  if (breakdownReview) {
    return { view: "taskBreakdownReview", breakdownId: decodeURIComponent(breakdownReview[1]) };
  }

  const board = normalized.match(/^\/(?:app\/)?projects\/([^/]+)\/board$/);
  if (board) return { view: "board", projectId: board[1] };

  const workspace = normalized.match(/^\/(?:app\/)?projects\/([^/]+)$/);
  if (workspace) return { view: "workspace", projectId: workspace[1] };

  const taskHistory = normalized.match(/^\/projects\/([^/]+)\/task-history$/);
  if (taskHistory) return { view: "taskHistory", projectId: decodeURIComponent(taskHistory[1]) };

  return { view: "notFound" };
}
