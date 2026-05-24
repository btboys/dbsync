<template>
  <div>
    <h2 class="ds-page-title">
      <t-icon name="rollback" class="ds-page-title-icon" />
      恢复管理
    </h2>

    <!-- 当前恢复进度 -->
    <div v-if="restoringRecord" class="ds-card" style="margin-bottom:20px;border-left:4px solid var(--ds-warning);">
      <div class="ds-card-header">
        <h3 class="ds-card-title">
          <t-icon name="loading" />
          当前恢复进度
        </h3>
        <t-tag theme="warning">
          <template #icon><t-icon name="loading" /></template>
          恢复中 {{ restoreElapsed }}
        </t-tag>
      </div>
      <div style="margin-bottom:8px;">
        <t-progress :percentage="50" status="active" :stroke-width="6" />
      </div>
      <div v-if="restoreLogs.length > 0" class="log-timeline">
        <div v-for="l in restoreLogs" :key="l.id" class="log-entry" :class="l.level">
          <span class="log-time">{{ fmtDatetime(l.created_at) }}</span>
          <t-tag :theme="l.level === 'error' ? 'danger' : l.level === 'warning' ? 'warning' : 'default'" size="small">{{ l.level }}</t-tag>
          <span class="log-msg">{{ l.message }}</span>
        </div>
      </div>
      <div v-else class="ds-empty" style="padding:16px">
        <t-loading loading size="small" indicator /> 等待任务启动...
      </div>
    </div>

    <div class="ds-card">
      <div class="ds-table-wrap">
        <t-table :data="backupStore.records" :columns="columns" row-key="id" :loading="backupStore.loading" hover stripe>
          <template #status="{ row }">
            <t-tag :theme="row.status === 'success' ? 'success' : row.status === 'cancelled' ? 'default' : 'danger'">
              {{ row.status === 'success' ? '成功' : row.status === 'cancelled' ? '已取消' : '失败' }}
            </t-tag>
          </template>
          <template #started_at="{ row }">
            {{ fmtDatetime(row.started_at) }}
          </template>
          <template #action="{ row }">
            <t-button v-if="row.status === 'success'" variant="text" theme="primary" @click="confirmRestore(row)">恢复</t-button>
          </template>
        </t-table>
      </div>
    </div>

    <t-dialog
      v-model:visible="confirmVisible"
      header="确认恢复"
      :body="confirmBody"
      confirm-btn="确认恢复"
      cancel-btn="取消"
      theme="warning"
      @confirm="executeRestore"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { MessagePlugin } from "tdesign-vue-next";
import { useBackupStore } from "../stores";
import { fmtDatetime } from "../utils/format";
import { api } from "../api/client";

const backupStore = useBackupStore();
const confirmVisible = ref(false);
const confirmBody = ref("");
const selectedRecord = ref<any>(null);

const restoringRecord = ref<any>(null);
const restoreLogs = ref<any[]>([]);
const restoreElapsed = ref("");
let restorePollTimer: ReturnType<typeof setInterval> | null = null;
let restoreElapsedTimer: ReturnType<typeof setInterval> | null = null;

const columns = [
  { colKey: "id", title: "ID", width: 80 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "file_path", title: "文件" },
  { colKey: "started_at", title: "时间" },
  { colKey: "action", title: "操作", width: 100 },
];

onMounted(async () => {
  await backupStore.fetchRecords();
});

onUnmounted(() => {
  stopRestorePolling();
  stopRestoreElapsedTimer();
});

function confirmRestore(row: any) {
  selectedRecord.value = row;
  confirmBody.value = `确定要从备份记录 #${row.id} 恢复吗？<br/>文件: ${row.file_path || '未知'}`;
  confirmVisible.value = true;
}

async function executeRestore() {
  if (!selectedRecord.value) return;
  confirmVisible.value = false;
  try {
    await backupStore.restoreRecord(selectedRecord.value.id);
    MessagePlugin.success("恢复任务已触发");
    restoringRecord.value = selectedRecord.value;
    restoreLogs.value = [];
    startRestoreElapsedTimer();
    startRestorePolling(selectedRecord.value.id);
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

function startRestoreElapsedTimer() {
  if (restoreElapsedTimer) clearInterval(restoreElapsedTimer);
  restoreElapsed.value = "0秒";
  let seconds = 0;
  restoreElapsedTimer = setInterval(() => {
    seconds++;
    if (seconds < 60) {
      restoreElapsed.value = `${seconds}秒`;
    } else {
      const m = Math.floor(seconds / 60);
      restoreElapsed.value = `${m}分${seconds % 60}秒`;
    }
  }, 1000);
}

function stopRestoreElapsedTimer() {
  if (restoreElapsedTimer) {
    clearInterval(restoreElapsedTimer);
    restoreElapsedTimer = null;
  }
}

async function fetchRestoreLogs(recordId: number) {
  try {
    const logs = await api.listTaskLogs({ task_type: "restore", task_record_id: recordId });
    restoreLogs.value = logs;
    // 如果有成功或错误日志，停止轮询
    const hasEnd = logs.some((l: any) => 
      l.message.includes("completed") || l.level === "error"
    );
    if (hasEnd) {
      stopRestorePolling();
      stopRestoreElapsedTimer();
      restoringRecord.value = null;
    }
  } catch {
    // ignore
  }
}

function startRestorePolling(recordId: number) {
  if (restorePollTimer) return;
  restorePollTimer = setInterval(() => {
    fetchRestoreLogs(recordId);
  }, 3000);
  // 立即获取一次
  fetchRestoreLogs(recordId);
}

function stopRestorePolling() {
  if (restorePollTimer) {
    clearInterval(restorePollTimer);
    restorePollTimer = null;
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
