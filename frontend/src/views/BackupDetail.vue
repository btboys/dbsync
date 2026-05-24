<template>
  <div v-if="task">
    <div class="ds-toolbar">
      <h2 class="ds-page-title" style="margin:0">
        <t-icon name="backup" class="ds-page-title-icon" />
        {{ task.name }}
      </h2>
      <t-space>
        <t-button theme="primary" @click="$router.push(`/backup/${task.id}/edit`)">
          <template #icon><t-icon name="edit" /></template>
          编辑
        </t-button>
        <t-button :loading="running" @click="handleRun">
          <template #icon><t-icon name="play" /></template>
          立即执行
        </t-button>
      </t-space>
    </div>

    <div class="ds-card" style="margin-bottom:20px">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">类型</div>
          <t-tag :color="task.backup_type === 'full' ? '#6366F1' : '#10B981'">{{ task.backup_type === 'full' ? '全量' : '增量' }}</t-tag>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">压缩</div>
          <div style="font-size: 14px;">{{ task.compression ? '是' : '否' }}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">保留天数</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 14px;">{{ task.retention_days }}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">定时</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 13px;">{{ task.schedule_config?.cron || '手动' }}</div>
        </div>
      </div>
    </div>

    <!-- Running task progress card -->
    <div v-if="currentRunning" class="ds-card" style="margin-bottom:20px;border-left:4px solid var(--ds-warning);">
      <div class="ds-card-header">
        <h3 class="ds-card-title">
          <t-icon name="loading" />
          当前执行进度
        </h3>
        <div style="display: flex; align-items: center; gap: 8px;">
          <t-tag theme="warning">
            <template #icon><t-icon name="loading" /></template>
            执行中 {{ elapsed }}
          </t-tag>
          <t-button theme="danger" variant="outline" size="small" :loading="cancelling" @click="handleCancel">
            取消任务
          </t-button>
        </div>
      </div>
      <div style="margin-bottom:8px;">
        <t-progress :percentage="50" :status="status === 'success' ? 'success' : status === 'fail' ? 'error' : 'active'" :stroke-width="6" />
      </div>
      <div v-if="taskLogs.length > 0" class="log-timeline">
        <div v-for="l in taskLogs" :key="l.id" class="log-entry" :class="l.level">
          <span class="log-time">{{ fmtDatetime(l.created_at) }}</span>
          <t-tag :theme="l.level === 'error' ? 'danger' : l.level === 'warning' ? 'warning' : 'default'" size="small">{{ l.level }}</t-tag>
          <span class="log-msg">{{ l.message }}</span>
        </div>
      </div>
      <div v-else class="ds-empty" style="padding:16px">
        <t-loading loading size="small" indicator /> 等待任务启动...
      </div>
    </div>

    <!-- Error banner for failed record -->
    <t-alert v-if="latestError" theme="error" :message="latestError" style="margin-bottom:12px" />

    <div class="ds-card">
      <div class="ds-card-header">
        <h3 class="ds-card-title">
          <t-icon name="file" />
          执行记录
        </h3>
      </div>
      <div class="ds-table-wrap">
        <t-table 
          :data="records" 
          :columns="recordColumns" 
          row-key="id" 
          hover 
          stripe
          :pagination="recordPagination"
          @page-change="onRecordPageChange"
        >
          <template #status="{ row }">
            <t-tag :theme="getStatusTheme(row.status)">
              <template v-if="row.status === 'running'" #icon><t-icon name="loading" /></template>
              {{ getStatusLabel(row.status) }}
            </t-tag>
          </template>
          <template #file_size="{ row }">
            <span v-if="row.uncompressed_size">
              {{ fmtBytes(row.uncompressed_size) }} <span style="color: var(--ds-text-secondary);">({{ fmtBytes(row.file_size) }})</span>
            </span>
            <span v-else>{{ fmtBytes(row.file_size) }}</span>
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
            <t-space>
              <t-button variant="text" theme="primary" @click="$router.push(`/backup/${task.id}/record/${row.id}`)">详情</t-button>
              <t-button variant="text" theme="danger" @click="confirmDeleteRecord(row)">删除</t-button>
            </t-space>
          </template>
        </t-table>
      </div>
    </div>

    <!-- Delete confirmation dialog -->
    <t-dialog
      v-model:visible="deleteDialogVisible"
      header="确认删除"
      theme="danger"
      @confirm="executeDeleteRecord"
    >
      <p>确定要删除备份记录 #{{ deleteTarget?.id }} 吗？</p>
      <p style="color: var(--ds-text-secondary); margin-top: 8px;">此操作将同时删除备份文件，不可恢复。</p>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";
import { fmtDatetime, fmtBytes } from "../utils/format";

const route = useRoute();
const task = ref<any>(null);
const records = ref<any[]>([]);
const taskLogs = ref<any[]>([]);
const running = ref(false);
const cancelling = ref(false);
let elapsedTimer: ReturnType<typeof setInterval> | null = null;
const elapsed = ref("");
let statusPollTimer: ReturnType<typeof setInterval> | null = null;
let processLogPollTimer: ReturnType<typeof setInterval> | null = null;

// Pagination
const recordPagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
});

// Delete dialog
const deleteDialogVisible = ref(false);
const deleteTarget = ref<any>(null);

const recordColumns = [
  { colKey: "id", title: "ID", width: 80 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "file_size", title: "大小", width: 160 },
  { colKey: "started_at", title: "开始时间", width: 160 },
  { colKey: "finished_at", title: "完成时间", width: 160 },
  { colKey: "duration", title: "运行时间", width: 120 },
  { colKey: "action", title: "操作", width: 120 },
];

const currentRunning = computed(() => records.value.find((r) => r.status === "running"));
const status = computed(() => currentRunning.value?.status || "");
const latestError = computed(() => {
  const failed = records.value.find((r) => r.status === "fail" && r.error_message);
  return failed?.error_message || null;
});

function toUtcTimestamp(val: string): number {
  const raw = val.includes("T") && !val.endsWith("Z") ? val + "Z" : val;
  return new Date(raw).getTime();
}

function formatElapsed(start: string) {
  const diff = Date.now() - toUtcTimestamp(start);
  if (diff < 0) return "0秒";
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}秒`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}分${s % 60}秒`;
  const h = Math.floor(m / 60);
  return `${h}小时${m % 60}分${s % 60}秒`;
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

function startElapsedTimer(start: string) {
  if (elapsedTimer) clearInterval(elapsedTimer);
  elapsed.value = formatElapsed(start);
  elapsedTimer = setInterval(() => {
    elapsed.value = formatElapsed(start);
  }, 1000);
}

function stopElapsedTimer() {
  if (elapsedTimer) {
    clearInterval(elapsedTimer);
    elapsedTimer = null;
  }
}

async function fetchProcessLogs(recordId: number) {
  try {
    const res = await api.listTaskProcessLogs({ task_type: "backup", task_record_id: recordId });
    taskLogs.value = res.items;
  } catch {
    // ignore
  }
}

function startProcessLogPolling(recordId: number) {
  if (processLogPollTimer) return;
  processLogPollTimer = setInterval(async () => {
    await fetchProcessLogs(recordId);
  }, 3000);
}

function stopProcessLogPolling() {
  if (processLogPollTimer) {
    clearInterval(processLogPollTimer);
    processLogPollTimer = null;
  }
}

async function fetchRecords() {
  const id = Number(route.params.id);
  try {
    const allRecords = await api.listBackupRecords(id);
    allRecords.sort((a: any, b: any) => b.id - a.id);
    recordPagination.value.total = allRecords.length;
    
    const start = (recordPagination.value.current - 1) * recordPagination.value.pageSize;
    const end = start + recordPagination.value.pageSize;
    records.value = allRecords.slice(start, end);
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

function onRecordPageChange(pageInfo: any) {
  recordPagination.value.current = pageInfo.current;
  recordPagination.value.pageSize = pageInfo.pageSize;
  fetchRecords();
}

function startStatusPolling() {
  if (statusPollTimer) return;
  statusPollTimer = setInterval(async () => {
    await fetchRecords();
    const runningRec = records.value.find((r) => r.status === "running");
    if (!runningRec) {
      stopStatusPolling();
      stopElapsedTimer();
      stopProcessLogPolling();
      // Refresh task info when done
      const id = Number(route.params.id);
      task.value = await api.getBackupTask(id);
    }
  }, 5000);
}

function stopStatusPolling() {
  if (statusPollTimer) {
    clearInterval(statusPollTimer);
    statusPollTimer = null;
  }
}

onMounted(async () => {
  const id = Number(route.params.id);
  task.value = await api.getBackupTask(id);
  await fetchRecords();
  const runningRec = records.value.find((r) => r.status === "running");
  if (runningRec) {
    await fetchProcessLogs(runningRec.id);
    startElapsedTimer(runningRec.started_at);
    startProcessLogPolling(runningRec.id);
    startStatusPolling();
  }
});

onUnmounted(() => {
  stopStatusPolling();
  stopElapsedTimer();
  stopProcessLogPolling();
});

async function handleRun() {
  running.value = true;
  try {
    await api.runBackupTask(task.value!.id);
    MessagePlugin.success("备份任务已触发");
    await fetchRecords();
    const runningRec = records.value.find((r) => r.status === "running");
    if (runningRec) {
      taskLogs.value = [];
      startElapsedTimer(runningRec.started_at);
      startProcessLogPolling(runningRec.id);
      startStatusPolling();
    }
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    running.value = false;
  }
}

async function handleCancel() {
  if (!currentRunning.value) return;
  cancelling.value = true;
  try {
    await api.cancelBackupRecord(currentRunning.value.id);
    MessagePlugin.success("任务已取消");
    await fetchRecords();
    stopElapsedTimer();
    stopStatusPolling();
    stopProcessLogPolling();
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    cancelling.value = false;
  }
}

function confirmDeleteRecord(row: any) {
  deleteTarget.value = row;
  deleteDialogVisible.value = true;
}

async function executeDeleteRecord() {
  if (!deleteTarget.value) return;
  try {
    await api.deleteBackupRecord(deleteTarget.value.id);
    MessagePlugin.success("备份记录已删除");
    deleteDialogVisible.value = false;
    await fetchRecords();
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    deleteTarget.value = null;
  }
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
</script>

<style scoped>
.log-timeline {
  max-height: 200px;
  overflow-y: auto;
}

.log-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
  font-family: 'Fira Code', monospace;
}

.log-time {
  color: var(--ds-text-secondary);
  font-size: 11px;
  white-space: nowrap;
  min-width: 140px;
}

.log-msg {
  flex: 1;
  word-break: break-all;
}
</style>
