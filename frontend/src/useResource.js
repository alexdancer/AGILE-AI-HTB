import { useEffect, useState } from "react";

import { getJSON } from "./api.js";

// Minimal load-once data hook: { data, error, loading } for a JSON endpoint.
export function useResource(url, refreshKey = 0) {
  const [state, setState] = useState({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let active = true;
    setState({ data: null, error: null, loading: true });
    getJSON(url)
      .then((data) => {
        if (active) setState({ data, error: null, loading: false });
      })
      .catch((error) => {
        if (active) setState({ data: null, error, loading: false });
      });
    return () => {
      active = false;
    };
  }, [url, refreshKey]);

  return state;
}
