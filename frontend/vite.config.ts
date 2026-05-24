import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const target = process.env.VITE_API_PROXY || "http://localhost:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    proxy: {
      "/api": target,
      "/ws": { target: target.replace("http", "ws"), ws: true },
    },
  },
});
