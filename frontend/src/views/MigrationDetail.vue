<template>
  <div v-if="task">
    <div class="ds-toolbar">
      <h2 class="ds-page-title" style="margin:0">
        <t-icon name="swap" class="ds-page-title-icon" />
        {{ task.name }}
      </h2>
      <t-space>
        <t-button theme="primary" @click="$router.push(`/migration/${task.id}/edit`)">
          <template #icon><t-icon name="edit" /></template>
          编辑
        </t-button>
        <t-button :loading="running" @click="handleRun">
          <template #icon><t-icon name="play" /></template>
          执行迁移
        </t-button>
      </t-space>
    </div>

    <div class="ds-card" style="margin-bottom:20px">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">迁移类型</div>
          <t-tag :color="task.transfer_type === 'schema_and_data' ? '#6366F1' : task.transfer_type === 'data_only' ? '#10B981' : '#F59E0B'">
            {{ task.transfer_type === 'schema_only' ? '仅结构' : task.transfer_type === 'data_only' ? '仅数据' : '结构+数据' }}
          </t-tag>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">源数据源</div>
          <div style="font-size: 14px;">{{ sourceName }}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">目标数据源</div>
          <div style="font-size: 14px;">{{ targetName }}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">包含表</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 13px;">{{ task.table_include?.join(', ') || '全部' }}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">排除表</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 13px;">{{ task.table_exclude?.join(', ') || '无' }}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">创建时间</div>
          <div style="font-size: 13px;">{{ fmtDatetime(task.created_at) }}</div>
        </div>
      </div>
    </div>

    <!-- 当前执行进度 -->
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
      
      <!-- 当前步骤标题 -->
      <div v-if="currentStep" class="step-title">
        {{ currentStep }}
      </div>
      
      <!-- 日志滚动区域 -->
      <div ref="logContainer" class="log-scroll-container">
        <div v-if="taskLogs.length > 0" class="log-content">
          <div v-for="l in taskLogs" :key="l.id" class="log-line" :class="l.level">
            <span class="log-time">{{ fmtDatetime(l.created_at) }}</span>
            <span class="log-separator">|</span>
            <span class="log-message">{{ l.message }}</span>
          </div>
        </div>
        <div v-else class="log-empty">
          <t-loading loading size="small" indicator /> 等待任务启动...
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <t-alert v-if="latestError" theme="error" :message="latestError" style="margin-bottom:12px" />

    <div class="ds-card">
      <div class="ds-card-header">
        <h3 class="ds-card-title">
          <t-icon name="file" />
          执行记录
        </h3>
      </div>
      <div class="ds-table-wrap">
        <t-table :data="records" :columns="recordColumns" row-key="id" hover stripe>
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
        </t-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";
import { fmtDatetime } from "../utils/format";

const route = useRoute();
const task = ref<any>(null);
const records = ref<any[]>([]);
const datasources = ref<any[]>([]);
const running = ref(false);
const cancelling = ref(false);

const taskLogs = ref<any[]>([]);
let elapsedTimer: ReturnType<typeof setInterval> | null = null;
const elapsed = ref("");
const logContainer = ref<HTMLElement | null>(null);
let eventSource: EventSource | null = null;
let statusPollTimer: ReturnType<typeof setInterval> | null = null;

const recordColumns = [
  { colKey: "id", title: "ID", width: 80 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "rows_transferred", title: "传输行数", width: 120 },
  { colKey: "started_at", title: "开始时间" },
  { colKey: "finished_at", title: "完成时间" },
  { colKey: "duration", title: "运行时间", width: 120 },
];

const currentRunning = computed(() => records.value.find((r) => r.status === "running"));
const currentStep = computed(() => {
  const stepLog = [...taskLogs.value].reverse().find((l) => 
    l.message && (l.message.startsWith("[步骤") || l.message.startsWith("[进度"))
  );
  return stepLog?.message || "";
});
const latestError = computed(() => {
  const failed = records.value.find((r) => r.status === "fail" && r.error_message);
  return failed?.error_message || null;
});

const sourceName = computed(() => {
  const ds = datasources.value.find((d) => d.id === task.value?.source_datasource_id);
  return ds ? `${ds.name} (${ds.type})` : `ID: ${task.value?.source_datasource_id}`;
});

const targetName = computed(() => {
  const ds = datasources.value.find((d) => d.id === task.value?.target_datasource_id);
  return ds ? `${ds.name} (${ds.type})` : `ID: ${task.value?.target_datasource_id}`;
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

function scrollToBottom() {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    }
  });
}

async function fetchProcessLogs(recordId: number) {
  try {
    const res = await api.listTaskProcessLogs({ task_type: "migration", task_record_id: recordId });
    taskLogs.value = res.items;
    scrollToBottom();
  } catch {
    // ignore
  }
}

let processLogPollTimer: ReturnType<typeof setInterval> | null = null;

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

function startStatusPolling() {
  if (statusPollTimer) return;
  const id = Number(route.params.id);
  statusPollTimer = setInterval(async () => {
    records.value = await api.listMigrationRecords(id);
    const runningRec = records.value.find((r) => r.status === "running");
    if (!runningRec) {
      stopStatusPolling();
      stopElapsedTimer();
      stopProcessLogPolling();
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
  datasources.value = await api.listDatasources();
  task.value = await api.getMigrationTask(id);
  records.value = await api.listMigrationRecords(id);
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
    await api.runMigrationTask(task.value!.id);
    MessagePlugin.success("迁移任务已触发");
    const id = Number(route.params.id);
    records.value = await api.listMigrationRecords(id);
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
    await api.cancelMigrationRecord(currentRunning.value.id);
    MessagePlugin.success("任务已取消");
    const id = Number(route.params.id);
    records.value = await api.listMigrationRecords(id);
    stopElapsedTimer();
    stopStatusPolling();
    stopProcessLogPolling();
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    cancelling.value = false;
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
.step-title {
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--ds-bg-secondary);
  border-radius: 6px;
  font-size: 14px;
  color: var(--ds-text-primary);
  font-weight: 500;
}

.log-scroll-container {
  max-height: 400px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 6px;
  padding: 12px;
  font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.log-line {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #d4d4d4;
  word-break: break-all;
}

.log-line.error {
  color: #f48771;
}

.log-line.warning {
  color: #dcdcaa;
}

.log-time {
  color: #858585;
  font-size: 11px;
  white-space: nowrap;
  min-width: 140px;
  flex-shrink: 0;
}

.log-separator {
  color: #858585;
  flex-shrink: 0;
}

.log-message {
  flex: 1;
}

.log-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: #858585;
}
</style>
