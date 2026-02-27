import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // FastAPI: http://localhost:8001
      "/chat": "http://localhost:8001",
      "/ingest": "http://localhost:8001",
    },
  },
});
