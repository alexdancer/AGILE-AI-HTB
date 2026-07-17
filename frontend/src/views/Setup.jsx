import React, { useState } from "react";

import { useResource } from "../useResource.js";

const safeError = (error) => error?.status === 401
  ? "Setup state requires sign-in."
  : "Could not load setup state. Retry.";

function setupAdapterQuery() {
  const search = typeof window !== "undefined" ? window.location.search : "";
  const adapterId = new URLSearchParams(search).get("adapter_id");
  return adapterId ? `?adapter_id=${encodeURIComponent(adapterId)}` : "";
}

export default function Setup() {
  const [query] = useState(() => setupAdapterQuery());
  const { data, error, loading } = useResource("/api/setup" + query, 0);

  return <SetupState data={data} error={error} loading={loading} />;
}

export function SetupState({ data, error, loading }) {
  if (loading && !data) {
    return <p className="spinner">Loading setup state…</p>;
  }
  if (error) {
    return (
      <>
        <div className="notice danger">{safeError(error)}</div>
        <p><a href="/setup">Retry</a></p>
      </>
    );
  }

  const setup = data || {};
  const steps = setup.steps || [];
  const nextStep = setup.next_step || { label: "", href: "", detail: "" };
  const activeAdapter = setup.active_adapter;
  const readyToLaunch = setup.ready_to_launch || false;

  const trackingLabel = trackingModeLabel(activeAdapter?.tracking_mode);

  return (
    <>
      <h1 className="page-title">First-run setup</h1>
      <p className="page-sub">
        connect control plane · confirm token budget · verify Worker token tracking · launch from board
      </p>

      <div className="live-notice" aria-live="polite">
        {readyToLaunch ? "Ready to launch" : "Complete the required setup steps before governed Worker launch."}
      </div>

      <section className="status-toolbar" aria-label="Next setup action">
        <div className="status-group">
          <span className={`pill ${readyToLaunch ? "green" : "yellow"}`}>
            {readyToLaunch ? "ready" : "next missing action"}
          </span>
          <span className="status-item">{nextStep.detail}</span>
        </div>
        <a className="btn primary" href={nextStep.href}>
          {nextStep.label}
        </a>
      </section>

      <section className="kpi-row" aria-label="Setup readiness">
        {steps.map((step) => (
          <article className="kpi" key={step.name}>
            <div className="label">{step.name}</div>
            <div className="value" style={{ fontSize: 18 }}>
              {step.state}
            </div>
            <div className="sub">{step.detail}</div>
            <p style={{ margin: "12px 0 0" }}>
              <a className="btn" href={step.href}>
                Open
              </a>
            </p>
          </article>
        ))}
      </section>

      <section className="panel" aria-label="Launch readiness">
        <div className="panel-header">
          <h3>Launch readiness</h3>
        </div>
        <div className="panel-body">
          {readyToLaunch ? (
            <>
              <p>
                <span className="pill green">ready</span> Worker execution has a confirmed budget, budget-authoritative adapter, and launch-ready Connected Project.
              </p>
              <p>
                <a className="btn primary" href={nextStep.href}>
                  Open task board
                </a>
              </p>
            </>
          ) : (
            <>
              <p>
                <span className="pill yellow">setup needed</span> Complete the required setup steps before governed Worker launch.
              </p>
              <ol>
                {steps.map((step) => (
                  <li key={step.name}>
                    <a href={step.href}>{step.name}</a>: {step.state}
                  </li>
                ))}
              </ol>
            </>
          )}
        </div>
      </section>

      {activeAdapter && (
        <section className="panel" aria-label="Active Worker adapter">
          <div className="panel-header">
            <h3>Active Worker adapter</h3>
          </div>
          <div className="panel-body">
            <dl className="workspace-kv">
              <dt>adapter</dt>
              <dd>{activeAdapter.name}</dd>
              <dt>status</dt>
              <dd>{activeAdapter.verification_status}</dd>
              <dt>launchable</dt>
              <dd>{activeAdapter.launchable ? "true" : "false"}</dd>
              <dt>tracking</dt>
              <dd>{trackingLabel}</dd>
            </dl>
          </div>
        </section>
      )}
    </>
  );
}

function trackingModeLabel(mode) {
  if (mode === null || mode === undefined) {
    return "unverified";
  }
  if (mode === "unverified") {
    return "unverified";
  }
  return String(mode);
}
