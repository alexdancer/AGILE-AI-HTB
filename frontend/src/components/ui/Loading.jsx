import React from "react";

import { cx } from "./cx.js";

// Inline loading line wrapping the shared `.spinner` class. Pass the message
// as children (e.g. <Loading>Loading Pipeline…</Loading>); it defaults to a
// generic label when omitted.
export function Loading({ className, children = "Loading…", ...rest }) {
  return (
    <p className={cx("spinner", className)} {...rest}>
      {children}
    </p>
  );
}
