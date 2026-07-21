// Tiny classname joiner for the UI primitives. Falsy parts are dropped so
// callers can write `cx("btn", size === "small" && "small", className)`.
export function cx(...parts) {
  return parts.filter(Boolean).join(" ");
}
