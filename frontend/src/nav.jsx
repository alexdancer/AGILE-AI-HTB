import React from "react";

// Client-side navigation for the React-owned canonical routes: dashboard, project
// workspace, and project board. App provides the navigate function; AppLink
// renders a real anchor so deep links, middle-click, and modifier-click open
// normally while plain clicks stay in-shell. The server-rendered login and
// missing-build recovery pages keep using ordinary <a> full navigations.
export const NavContext = React.createContext(() => {});
export const NavigationGuardContext = React.createContext(() => {});

export function AppLink({ to, className, children }) {
  const navigate = React.useContext(NavContext);
  const onClick = (event) => {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }
    event.preventDefault();
    navigate(to);
  };
  return (
    <a className={className} href={to} onClick={onClick}>
      {children}
    </a>
  );
}
