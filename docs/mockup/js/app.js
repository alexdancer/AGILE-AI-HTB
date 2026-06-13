// AGILE-AI-HTB — tiny render helpers shared by all mockup pages.
// Zero dependencies. Edit freely; this is a mockup, not production.

(function () {
  "use strict";

  const F = window.AGILE_AI_HTB.fixtures;

  // ---- Number / time formatting ---------------------------------------
  function fmt(n) { return Number(n).toLocaleString("en-US"); }
  function pct(used, cap) {
    if (!cap) return "—";
    return ((used / cap) * 100).toFixed(1) + "%";
  }
  function shortTs(iso) { return iso ? iso.substring(11, 19) : "—"; }
  function shortDate(iso) { return iso ? iso.substring(0, 10) : "—"; }

  // ---- Active nav highlight ------------------------------------------
  function highlightNav() {
    const here = (location.pathname.split("/").pop() || "index.html").toLowerCase();
    document.querySelectorAll(".sidebar a[data-page]").forEach((a) => {
      if (a.dataset.page.toLowerCase() === here) a.classList.add("active");
    });
  }

  // ---- Shared shell (topbar + sidebar + footer) -----------------------
  function renderShell(pageTitle) {
    const sidebar = document.querySelector(".sidebar");
    if (sidebar && !sidebar.dataset.rendered) {
      sidebar.dataset.rendered = "1";
      sidebar.innerHTML = `
        <div class="group">Governance</div>
        <nav>
          <a href="index.html"     data-page="index.html">Dashboard</a>
          <a href="sessions.html"  data-page="sessions.html">Sessions</a>
          <a href="alarms.html"    data-page="alarms.html">Alarms</a>
        </nav>
        <div class="group">Planning</div>
        <nav>
          <a href="estimate.html"  data-page="estimate.html">Estimate Task</a>
        </nav>
        <div class="group">Runtime</div>
        <nav>
          <a href="proxy.html"     data-page="proxy.html">Live Proxy</a>
        </nav>`;
    }

    const topbar = document.querySelector(".topbar");
    if (topbar && !topbar.dataset.rendered) {
      topbar.dataset.rendered = "1";
      topbar.innerHTML = `
        <div class="brand">AGILE-AI-HTB<span class="dot">·</span><span style="color:var(--fg-1)">Portal</span></div>
        <div class="meta">demo build · ${shortDate(F.meta.generated_at)} · ${F.meta.project}</div>`;
    }

    const footer = document.querySelector("footer");
    if (footer && !footer.dataset.rendered) {
      footer.dataset.rendered = "1";
      footer.textContent = "AGILE-AI-HTB mockup · synthetic data only · not connected to a live harness";
    }

    const t = document.querySelector(".page-title");
    if (t && pageTitle) t.textContent = pageTitle;
    highlightNav();
  }

  // ---- Severity / zone pills ------------------------------------------
  function zonePill(zone) {
    const cls = zone === "green" ? "green" : zone === "yellow" ? "yellow" : zone === "red" ? "red" : "muted";
    return `<span class="pill ${cls}">zone: ${zone}</span>`;
  }
  function sevPill(sev) {
    const cls = sev === "critical" ? "red" : sev === "warning" ? "yellow" : "info";
    return `<span class="pill ${cls}">${sev}</span>`;
  }
  function statusPill(status) {
    const map = { active: "blue", paused: "yellow", completed: "green", blocked: "red", done: "green", backlog: "muted" };
    return `<span class="pill ${map[status] || "muted"}">${status}</span>`;
  }

  // ---- Resolve form (alarms) -----------------------------------------
  function resolveForm(alarmId) {
    return `
      <form class="btn-row" onsubmit="return AGILE_AI_HTB.app.dummyResolve(event, '${alarmId}')">
        <select name="action" style="max-width:200px">
          <option value="continue">Continue</option>
          <option value="abort_session">Abort session</option>
          <option value="raise_budget">Raise budget</option>
          <option value="adjust_guardrail">Adjust guardrail</option>
        </select>
        <button class="btn primary" type="submit">Resolve</button>
      </form>`;
  }

  function dummyResolve(ev, alarmId) {
    ev.preventDefault();
    const action = ev.target.action.value;
    const card = document.getElementById("alarm-" + alarmId);
    if (card) {
      card.style.opacity = "0.5";
      card.querySelector(".reco").textContent = `Resolved (mock) — action=${action}`;
    }
    return false;
  }

  // Export
  window.AGILE_AI_HTB.app = {
    fmt, pct, shortTs, shortDate,
    renderShell,
    zonePill, sevPill, statusPill,
    resolveForm, dummyResolve,
  };
})();
