import { defineConfig } from "vite";
import uniPluginModule from "@dcloudio/vite-plugin-uni";

const uni = typeof uniPluginModule === "function" ? uniPluginModule : uniPluginModule.default;

export default defineConfig({
  plugins: [uni()]
});
