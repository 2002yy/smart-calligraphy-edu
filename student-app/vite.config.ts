import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5175,
    strictPort: true,
    hmr: {
      clientPort: 443
    },
    headers: {
      'Access-Control-Allow-Origin': '*',
    }
  },
  preview: {
    host: "0.0.0.0",
    port: 4175,
    strictPort: true,
    allowedHosts: true
  },
  test: {
    environment: "happy-dom",
    globals: true,
    include: ["src/**/*.{test,spec}.{ts,js}"],
  }
});