import { createApp } from "vue";
import { createPinia } from "pinia";
import TDesign from "tdesign-vue-next";
import "tdesign-vue-next/es/style/index.css";
import "./assets/design-system.css";
import {
  DashboardIcon,
  ServerIcon,
  BackupIcon,
  RollbackIcon,
  SwapIcon,
  TimeIcon,
  FileIcon,
  ViewListIcon,
} from "tdesign-icons-vue-next";

import App from "./App.vue";
import router from "./router";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(TDesign);

// Register icons globally
const icons = { DashboardIcon, ServerIcon, BackupIcon, RollbackIcon, SwapIcon, TimeIcon, FileIcon, ViewListIcon };
Object.entries(icons).forEach(([name, comp]) => {
  app.component(name, comp);
});

app.mount("#app");
