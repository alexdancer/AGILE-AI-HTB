import React from "react";

import { cx } from "./cx.js";

// Wraps the shared `.btn` class vocabulary from tokens.css. Polymorphic via
// `as` so the same button styling covers real <button>s, in-shell AppLink
// navigation, and plain <a> links without repeating the class string across
// views. `variant` maps to the tone classes (primary is the bare `.btn`),
// `size="small"` adds `.small`. Any other prop (type, onClick, href, to,
// disabled, aria-*) passes straight through to the underlying element.
export function Button({
  as: Component = "button",
  variant = "primary",
  size,
  className,
  children,
  ...rest
}) {
  const classes = cx(
    "btn",
    size === "small" && "small",
    variant && variant !== "primary" && variant,
    className,
  );
  return (
    <Component className={classes} {...rest}>
      {children}
    </Component>
  );
}
