import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import router from "./router";
import "./styles.css";

const app = createApp(App);

app.config.errorHandler = (error) => {
  const message = error instanceof Error ? error.message : "页面运行时发生异常。";
  window.dispatchEvent(new CustomEvent("app-runtime-error", { detail: { message } }));
};

app.use(createPinia());
app.use(router);
app.mount("#app");
