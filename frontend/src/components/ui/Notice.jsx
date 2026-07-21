import React from "react";

import { cx } from "./cx.js";

// Inline message wrapping the shared `.notice` class. `variant` is info
// (bare `.notice`), warning, or danger. `role` passes through so callers can
// mark live error notices with role="alert" where it belongs.
export function Notice({ variant = "info", className, children, ...rest }) {
  return (
    <div className={cx("notice", variant !== "info" && variant, className)} {...rest}>
      {children}
    </div>
  );
}
