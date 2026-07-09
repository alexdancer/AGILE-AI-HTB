import React from "react";

// Non-migrated Portal surfaces stay server-rendered by FastAPI/Jinja. The shell
// links back to them so operators can move between the React surface and the
// existing pages during migration.
const JINJA_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/setup", label: "Setup" },
  { href: "/settings/workers", label: "Settings" },
  { href: "/sessions", label: "Sessions" },
  { href: "/alarms", label: "Alarms" },
];

export default function Shell({ children }) {
  return (
    <>
      <header className="topbar">
        <span className="brand">
          AGILE-AI-HTB<span className="dot">·</span>Portal
        </span>
        <nav className="topbar-nav" aria-label="Portal navigation">
          {JINJA_LINKS.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
      </header>
      <main className="content">{children}</main>
    </>
  );
}
