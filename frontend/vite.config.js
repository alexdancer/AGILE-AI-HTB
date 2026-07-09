import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The built shell is served by FastAPI from `src/agile_ai_htb/static/react`,
// and every asset is referenced under `/static/react/` so the FastAPI asset
// route can resolve it. There is no separate Node server in production.
export default defineConfig({
  plugins: [react()],
  base: "/static/react/",
  build: {
    outDir: "../src/agile_ai_htb/static/react",
    emptyOutDir: true,
  },
});
