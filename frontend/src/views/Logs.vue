<template>
  <div>
    <h2 class="ds-page-title">
      <t-icon name="file" class="ds-page-title-icon" />
      执行记录
    </h2>

    <!-- Running tasks banner -->
    <div v-if="runningTasks.length > 0" class="ds-card" style="margin-bottom:16px">
      <div class="ds-card-header">
        <h3 class="ds-card-title">
          <t-icon name="loading" />
          执行中的任务
        </h3>
      </div>
      <div v-for="t in runningTasks" :key="t.key" class="running-task-row">
        <t-tag :color="t.type === 'backup' ? '#6366F1' : '#10B981'">{{ t.type === 'backup' ? '备份' : '迁移' }}</t-tag>
        <span class="task-name">{{ t.name }}</span>
        <t-tag theme="warning">
          <template #icon><t-icon name="loading" /></template>
          执行中
        </t-tag>
        <span class="task-time">{{ fmtDatetime(t.started_at) }}</span>
        <t-button variant="text" theme="primary" size="small" @click="goToDetail(t)">查看</t-button>
      </div>
    </div>

    <!-- Tab 切换 -->
    <t-tabs v-model="activeTab" @change="onTabChange">
      <t-tab-panel value="backup" label="备份">
        <div class="ds-table-wrap">
          <t-table 
            :data="backupRecords" 
            :columns="backupColumns" 
            row-key="id" 
            :loading="loading"
            :pagination="backupPagination"
            @page-change="onBackupPageChange"
            hover 
            stripe
          >
            <template #status="{ row }">
              <t-tag :theme="getStatusTheme(row.status)">
                <template v-if="row.status === 'running'" #icon><t-icon name="loading" /></template>
                {{ getStatusLabel(row.status) }}
              </t-tag>
            </template>
            <template #file_size="{ row }">
              {{ fmtBytes(row.file_size) }}
            </template>
            <template #started_at="{ row }">
              {{ fmtDatetime(row.started_at) }}
            </template>
            <template #finished_at="{ row }">
              {{ fmtDatetime(row.finished_at) }}
            </template>
            <template #duration="{ row }">
              {{ formatDuration(row.started_at, row.finished_at) }}
            </template>
            <template #action="{ row }">
              <t-button variant="text" theme="primary" size="small" @click="goToBackupDetail(row)">详情</t-button>
            </template>
          </t-table>
        </div>
      </t-tab-panel>

      <t-tab-panel value="migration" label="迁移">
        <div class="ds-table-wrap">
          <t-table 
            :data="migrationRecords" 
            :columns="migrationColumns" 
            row-key="id" 
            :loading="loading"
            :pagination="migrationPagination"
            @page-change="onMigrationPageChange"
            hover 
            stripe
          >
            <template #status="{ row }">
              <t-tag :theme="getStatusTheme(row.status)">
                <template v-if="row.status === 'running'" #icon><t-icon name="loading" /></template>
                {{ getStatusLabel(row.status) }}
              </t-tag>
            </template>
            <template #rows_transferred="{ row }">
              {{ row.rows_transferred ?? '-' }}
            </template>
            <template #started_at="{ row }">
              {{ fmtDatetime(row.started_at) }}
            </template>
            <template #finished_at="{ row }">
              {{ fmtDatetime(row.finished_at) }}
            </template>
            <template #duration="{ row }">
              {{ formatDuration(row.started_at, row.finished_at) }}
            </template>
            <template #action="{ row }">
              <t-button variant="text" theme="primary" size="small" @click="goToMigrationDetail(row)">详情</t-button>
            </template>
          </t-table>
        </div>
      </t-tab-panel>

      <t-tab-panel value="restore" label="恢复">
        <div class="ds-table-wrap">
          <t-table 
            :data="restoreRecords" 
            :columns="restoreColumns" 
            row-key="id" 
            :loading="loading"
            :pagination="restorePagination"
            @page-change="onRestorePageChange"
            hover 
            stripe
          >
            <template #status="{ row }">
              <t-tag :theme="getStatusTheme(row.status)">
                <template v-if="row.status === 'running'" #icon><t-icon name="loading" /></template>
                {{ getStatusLabel(row.status) }}
              </t-tag>
            </template>
            <template #started_at="{ row }">
              {{ fmtDatetime(row.started_at) }}
            </template>
            <template #finished_at="{ row }">
              {{ fmtDatetime(row.finished_at) }}
            </template>
            <template #duration="{ row }">
              {{ formatDuration(row.started_at, row.finished_at) }}
            </template>
            <template #action="{ row }">
              <t-button variant="text" theme="primary" size="small" @click="goToRestoreDetail(row)">详情</t-button>
            </template>
          </t-table>
        </div>
      </t-tab-panel>
    </t-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api/client";
import { MessagePlugin } from "tdesign-vue-next";
import { fmtDatetime } from "../utils/format";

const router = useRouter();
const activeTab = ref("backup");
const loading = ref(false);
const runningTasks = ref<any[]>([]);
let pollTimer: ReturnType<typeof setInterval> | null = null;

// 备份
const backupRecords = ref<any[]>([]);
const backupPagination = ref({ current: 1, pageSize: 20, total: 0 });

// 迁移
const migrationRecords = ref<any[]>([]);
const migrationPagination = ref({ current: 1, pageSize: 20, total: 0 });

// 恢复
const restoreRecords = ref<any[]>([]);
const restorePagination = ref({ current: 1, pageSize: 20, total: 0 });

const backupColumns = [
  { colKey: "id", title: "ID", width: 80 },
  { colKey: "task_name", title: "任务名称", width: 180 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "file_size", title: "文件大小", width: 120 },
  { colKey: "message", title: "消息" },
  { colKey: "started_at", title: "开始时间", width: 160 },
  { colKey: "finished_at", title: "结束时间", width: 160 },
  { colKey: "duration", title: "执行时间", width: 120 },
  { colKey: "action", title: "操作", width: 80 },
];

const migrationColumns = [
  { colKey: "id", title: "ID", width: 80 },
  { colKey: "task_name", title: "任务名称", width: 180 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "rows_transferred", title: "传输行数", width: 120 },
  { colKey: "message", title: "消息" },
  { colKey: "started_at", title: "开始时间", width: 160 },
  { colKey: "finished_at", title: "结束时间", width: 160 },
  { colKey: "duration", title: "执行时间", width: 120 },
  { colKey: "action", title: "操作", width: 80 },
];

const restoreColumns = [
  { colKey: "id", title: "ID", width: 80 },
  { colKey: "backup_name", title: "备份名称", width: 200 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "message", title: "消息" },
  { colKey: "started_at", title: "开始时间", width: 160 },
  { colKey: "finished_at", title: "结束时间", width: 160 },
  { colKey: "duration", title: "执行时间", width: 120 },
  { colKey: "action", title: "操作", width: 80 },
];

function toUtcTimestamp(val: string): number {
  const raw = val.includes("T") && !val.endsWith("Z") ? val + "Z" : val;
  return new Date(raw).getTime();
}

function formatDuration(start: string, finish: string | null) {
  if (!start || !finish) return "-";
  const diff = toUtcTimestamp(finish) - toUtcTimestamp(start);
  if (diff < 0) return "-";
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}秒`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}分${s % 60}秒`;
  const h = Math.floor(m / 60);
  return `${h}小时${m % 60}分${s % 60}秒`;
}

function getStatusTheme(status: string) {
  switch (status) {
    case "success": return "success";
    case "running": return "warning";
    case "cancelled": return "default";
    default: return "danger";
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case "success": return "成功";
    case "running": return "执行中";
    case "cancelled": return "已取消";
    default: return "失败";
  }
}

function fmtBytes(n: number | null) {
  if (!n) return "-";
  let num = n;
  for (const u of ["B", "KB", "MB", "GB"]) {
    if (num < 1024) return `${num.toFixed(1)} ${u}`;
    num /= 1024;
  }
  return `${num.toFixed(1)} TB`;
}

async function fetchRunningTasks() {
  try {
    const [backupRecords, migrationRecords, backupTasks, migrationTasks] = await Promise.all([
      api.listBackupRecords(undefined, "running"),
      api.listMigrationRecords(undefined, "running"),
      api.listBackupTasks(),
      api.listMigrationTasks(),
    ]);
    const btMap = Object.fromEntries(backupTasks.map((t: any) => [t.id, t]));
    const mtMap = Object.fromEntries(migrationTasks.map((t: any) => [t.id, t]));
    runningTasks.value = [
      ...backupRecords.map((r: any) => ({
        key: `b-${r.id}`, type: "backup", name: btMap[r.task_id]?.name || `Task #${r.task_id}`,
        id: r.task_id, recordId: r.id, started_at: r.started_at,
      })),
      ...migrationRecords.map((r: any) => ({
        key: `m-${r.id}`, type: "migration", name: mtMap[r.task_id]?.name || `Task #${r.task_id}`,
        id: r.task_id, recordId: r.id, started_at: r.started_at,
      })),
    ];
  } catch {
    // ignore poll errors
  }
}

function goToDetail(t: any) {
  if (t.type === "backup") {
    router.push(`/backup/${t.id}`);
  } else {
    router.push(`/migration/${t.id}`);
  }
}

function goToBackupDetail(row: any) {
  router.push({
    path: "/log-detail",
    query: { task_type: "backup", task_record_id: row.id },
  });
}

function goToMigrationDetail(row: any) {
  router.push({
    path: "/log-detail",
    query: { task_type: "migration", task_record_id: row.id },
  });
}

function goToRestoreDetail(row: any) {
  router.push({
    path: "/log-detail",
    query: { task_type: "restore", task_record_id: row.task_record_id },
  });
}

async function fetchBackupRecords() {
  try {
    const offset = (backupPagination.value.current - 1) * backupPagination.value.pageSize;
    const [records, tasks] = await Promise.all([
      api.listBackupRecords(),
      api.listBackupTasks(),
    ]);
    const taskMap = Object.fromEntries(tasks.map((t: any) => [t.id, t]));
    
    const items = records.map((r: any) => ({
      id: r.id,
      task_name: taskMap[r.task_id]?.name || `备份任务 #${r.task_id}`,
      status: r.status,
      file_size: r.file_size,
      message: r.error_message || (r.status === "success" ? `备份完成` : r.status === "running" ? "备份执行中..." : "备份失败"),
      started_at: r.started_at,
      finished_at: r.finished_at,
    }));
    
    items.sort((a: any, b: any) => b.id - a.id);
    const start = offset;
    const end = offset + backupPagination.value.pageSize;
    backupRecords.value = items.slice(start, end);
    backupPagination.value.total = items.length;
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

async function fetchMigrationRecords() {
  try {
    const offset = (migrationPagination.value.current - 1) * migrationPagination.value.pageSize;
    const [records, tasks] = await Promise.all([
      api.listMigrationRecords(),
      api.listMigrationTasks(),
    ]);
    const taskMap = Object.fromEntries(tasks.map((t: any) => [t.id, t]));
    
    const items = records.map((r: any) => ({
      id: r.id,
      task_name: taskMap[r.task_id]?.name || `迁移任务 #${r.task_id}`,
      status: r.status,
      rows_transferred: r.rows_transferred,
      message: r.error_message || (r.status === "success" ? `迁移完成，传输 ${r.rows_transferred || 0} 行` : r.status === "running" ? "迁移执行中..." : "迁移失败"),
      started_at: r.started_at,
      finished_at: r.finished_at,
    }));
    
    items.sort((a: any, b: any) => b.id - a.id);
    const start = offset;
    const end = offset + migrationPagination.value.pageSize;
    migrationRecords.value = items.slice(start, end);
    migrationPagination.value.total = items.length;
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

async function fetchRestoreRecords() {
  try {
    const offset = (restorePagination.value.current - 1) * restorePagination.value.pageSize;
    const res = await api.listRestoreRecords({
      limit: restorePagination.value.pageSize,
      offset: offset,
    });
    restoreRecords.value = res.items;
    restorePagination.value.total = res.total;
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

async function onTabChange(tab: string) {
  activeTab.value = tab;
  loading.value = true;
  try {
    if (tab === "backup") await fetchBackupRecords();
    else if (tab === "migration") await fetchMigrationRecords();
    else if (tab === "restore") await fetchRestoreRecords();
  } finally {
    loading.value = false;
  }
}

function onBackupPageChange(pageInfo: any) {
  backupPagination.value.current = pageInfo.current;
  backupPagination.value.pageSize = pageInfo.pageSize;
  fetchBackupRecords();
}

function onMigrationPageChange(pageInfo: any) {
  migrationPagination.value.current = pageInfo.current;
  migrationPagination.value.pageSize = pageInfo.pageSize;
  fetchMigrationRecords();
}

function onRestorePageChange(pageInfo: any) {
  restorePagination.value.current = pageInfo.current;
  restorePagination.value.pageSize = pageInfo.pageSize;
  fetchRestoreRecords();
}

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(async () => {
    await fetchRunningTasks();
    if (runningTasks.value.length === 0) {
      stopPolling();
    }
  }, 3000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

onMounted(async () => {
  loading.value = true;
  try {
    await Promise.all([fetchBackupRecords(), fetchRunningTasks()]);
  } finally {
    loading.value = false;
  }
  if (runningTasks.value.length > 0) startPolling();
});

onUnmounted(() => stopPolling());
</script>

<style scoped>
.running-task-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--ds-border);
}

.running-task-row:last-child {
  border-bottom: none;
}

.task-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.task-time {
  font-size: 12px;
  color: var(--ds-text-secondary);
  font-family: 'Fira Code', monospace;
}
</style>
