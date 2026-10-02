import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// The .env file lives in the project root, one folder up. Only VITE_ variables ever reach the browser.
export default defineConfig(({ mode }) => {
  const here = import.meta.dirname;
  const env = loadEnv(mode, path.resolve(here, ".."), "VITE_");
  return {
    envDir: "..",
    plugins: [react(), tailwindcss()],
    resolve: { alias: { "@": path.resolve(here, "src") } },
    server: {
      port: 5173,
      // The browser always calls /api on this same address; Vite forwards it to the backend.
      proxy: { "/api": { target: env.VITE_API_PROXY_TARGET || "http://localhost:8000", changeOrigin: true } },
    },
    test: { environment: "node" },
  };
});
