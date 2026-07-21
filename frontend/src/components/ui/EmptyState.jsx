import React from "react";

import { cx } from "./cx.js";

// Empty / zero-result placeholder wrapping the shared `.empty-state` class.
// The message should teach the surface, not just say "nothing here".
export function EmptyState({ className, children, ...rest }) {
  return (
    <div className={cx("empty-state", className)} {...rest}>
      {children}
    </div>
  );
}
