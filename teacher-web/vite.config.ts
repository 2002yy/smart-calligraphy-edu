import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5174,
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
    port: 4174,
    strictPort: true,
    allowedHosts: true
  },
  test: {
    environment: "happy-dom",
    globals: true,
    include: ["src/**/*.{test,spec}.{ts,js}"],
  }
});