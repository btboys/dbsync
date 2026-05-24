import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "dashboard", component: () => import("../views/Dashboard.vue") },
    { path: "/datasources", name: "datasources", component: () => import("../views/DatasourceList.vue") },
    { path: "/datasources/:id", name: "datasource-detail", component: () => import("../views/DatasourceDetail.vue") },
    { path: "/backup", name: "backup", component: () => import("../views/BackupList.vue") },
    { path: "/backup/create", name: "backup-create", component: () => import("../views/BackupCreate.vue") },
    { path: "/backup/:id", name: "backup-detail", component: () => import("../views/BackupDetail.vue") },
    { path: "/backup/:id/record/:rid", name: "backup-record", component: () => import("../views/BackupRecord.vue") },
    { path: "/restore", name: "restore", component: () => import("../views/Restore.vue") },
    { path: "/migration", name: "migration", component: () => import("../views/MigrationList.vue") },
    { path: "/migration/create", name: "migration-create", component: () => import("../views/MigrationCreate.vue") },
    { path: "/migration/:id", name: "migration-detail", component: () => import("../views/MigrationDetail.vue") },
    { path: "/schedules", name: "schedules", component: () => import("../views/Schedules.vue") },
    { path: "/logs", name: "logs", component: () => import("../views/Logs.vue") },
  ],
});

export default router;
