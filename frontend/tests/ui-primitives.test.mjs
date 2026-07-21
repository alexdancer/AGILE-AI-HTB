import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const frontendRoot = fileURLToPath(new URL("../", import.meta.url));
let server;
let Button;
let Pill;
let Notice;
let EmptyState;
let Loading;
let Panel;
let PanelHeader;
let PanelBody;

before(async () => {
  server = await createServer({
    root: frontendRoot,
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({ Button, Pill, Notice, EmptyState, Loading, Panel, PanelHeader, PanelBody } =
    await server.ssrLoadModule("/src/components/ui/index.js"));
});

after(async () => {
  await server?.close();
});

const html = (element) => renderToStaticMarkup(element);

test("Button maps variant and size onto the shared .btn classes", () => {
  assert.match(html(React.createElement(Button, {}, "Go")), /^<button class="btn">Go<\/button>$/);
  assert.match(
    html(React.createElement(Button, { size: "small" }, "Go")),
    /class="btn small"/,
  );
  assert.match(
    html(React.createElement(Button, { size: "small", variant: "secondary" }, "Go")),
    /class="btn small secondary"/,
  );
  assert.match(
    html(React.createElement(Button, { variant: "danger" }, "Go")),
    /class="btn danger"/,
  );
});

test("Button is polymorphic and forwards arbitrary props", () => {
  const asAnchor = html(React.createElement(Button, { as: "a", href: "/x", variant: "secondary", size: "small" }, "Link"));
  assert.match(asAnchor, /^<a class="btn small secondary" href="\/x">Link<\/a>$/);

  const withType = html(React.createElement(Button, { type: "submit", disabled: true }, "Save"));
  assert.match(withType, /type="submit"/);
  assert.match(withType, /disabled/);
});

test("Pill keeps its tone modifier and text label", () => {
  assert.match(html(React.createElement(Pill, { tone: "green" }, "ready")), /^<span class="pill green">ready<\/span>$/);
  assert.match(html(React.createElement(Pill, {}, "idle")), /^<span class="pill">idle<\/span>$/);
});

test("Notice maps variant to the shared classes and forwards role", () => {
  assert.match(html(React.createElement(Notice, {}, "fyi")), /^<div class="notice">fyi<\/div>$/);
  assert.match(html(React.createElement(Notice, { variant: "warning" }, "w")), /class="notice warning"/);
  assert.match(
    html(React.createElement(Notice, { variant: "danger", role: "alert" }, "e")),
    /class="notice danger" role="alert"/,
  );
});

test("EmptyState and Loading wrap their shared classes", () => {
  assert.match(html(React.createElement(EmptyState, {}, "nothing here")), /^<div class="empty-state">nothing here<\/div>$/);
  assert.match(html(React.createElement(Loading, {}, "Loading Pipeline…")), /^<p class="spinner">Loading Pipeline…<\/p>$/);
  assert.match(html(React.createElement(Loading, {})), /Loading…/);
});

test("Panel trio composes header markers three ways", () => {
  const withCount = html(React.createElement(PanelHeader, { title: "Estimated", count: 3 }));
  assert.match(withCount, /<div class="panel-header"><h3>Estimated<\/h3><span class="column-count">3<\/span><\/div>/);

  const badge = html(React.createElement(PanelHeader, { title: "Needs You", badge: React.createElement("span", { className: "nav-badge" }, 2) }));
  assert.match(badge, /<span class="nav-badge">2<\/span>/);
  assert.doesNotMatch(badge, /column-count/);

  const bare = html(React.createElement(PanelHeader, { title: "Only" }));
  assert.match(bare, /^<div class="panel-header"><h3>Only<\/h3><\/div>$/);

  const panel = html(
    React.createElement(Panel, { className: "planning-inbox", id: "p" },
      React.createElement(PanelBody, { className: "needs-you-list" }, "body")),
  );
  assert.match(panel, /^<section class="panel planning-inbox" id="p">/);
  assert.match(panel, /<div class="panel-body needs-you-list">body<\/div>/);

  const asHeader = html(React.createElement(Panel, { as: "header", className: "pipeline-header" }, "x"));
  assert.match(asHeader, /^<header class="panel pipeline-header">x<\/header>$/);
});
