import React from "react";

import { cx } from "./cx.js";

// The workhorse container trio, wrapping the shared `.panel` / `.panel-header`
// / `.panel-body` classes.
//
// `Panel` is polymorphic (`as`, default <section>) so it also covers the
// `.pipeline-header.panel` <header> shape; extra classes and `id` pass through.
//
// `PanelHeader` renders the `<h3>` title plus an optional trailing marker.
// Most headers show a `.column-count`, so passing `count` renders that; for
// the few headers that need a different marker (a `.nav-badge`, a bare
// `<span>`), pass a ready-made node as `badge` and it wins.
export function Panel({ as: Component = "section", className, children, ...rest }) {
  return (
    <Component className={cx("panel", className)} {...rest}>
      {children}
    </Component>
  );
}

export function PanelHeader({ title, count, badge }) {
  return (
    <div className="panel-header">
      <h3>{title}</h3>
      {badge != null
        ? badge
        : count != null
          ? <span className="column-count">{count}</span>
          : null}
    </div>
  );
}

export function PanelBody({ className, children, ...rest }) {
  return (
    <div className={cx("panel-body", className)} {...rest}>
      {children}
    </div>
  );
}
