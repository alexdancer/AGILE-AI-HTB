import React from "react";

import { cx } from "./cx.js";

// Status marker wrapping the shared `.pill` class. `tone` is the semantic
// modifier (green / yellow / red / blue / running / idle / purple / …) that
// recolors border and text together. Callers compute the tone; the label text
// always states the status so meaning never rests on color alone.
export function Pill({ tone, className, children, ...rest }) {
  return (
    <span className={cx("pill", tone, className)} {...rest}>
      {children}
    </span>
  );
}
