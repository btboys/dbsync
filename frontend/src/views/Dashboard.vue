<template>
  <div>
    <h2 class="ds-page-title">
      <t-icon name="dashboard" class="ds-page-title-icon" />
      仪表盘
    </h2>

    <div class="ds-kpi-grid">
      <div class="ds-kpi">
        <div class="ds-kpi-label">数据源</div>
        <div class="ds-kpi-value">{{ stats.datasources }}</div>
        <div class="ds-kpi-sub">
          <t-icon name="server" /> 数据库连接
        </div>
      </div>
      <div class="ds-kpi">
        <div class="ds-kpi-label">备份任务</div>
        <div class="ds-kpi-value">{{ stats.backupTasks }}</div>
        <div class="ds-kpi-sub">
          <t-icon name="backup" /> 定时 + 手动
        </div>
      </div>
      <div class="ds-kpi cta">
        <div class="ds-kpi-label">迁移任务</div>
        <div class="ds-kpi-value">{{ stats.migrationTasks }}</div>
        <div class="ds-kpi-sub">
          <t-icon name="swap" /> 跨库传输
        </div>
      </div>
      <div class="ds-kpi warning">
        <div class="ds-kpi-label">正在运行</div>
        <div class="ds-kpi-value">{{ runningTasks.length }}</div>
        <div class="ds-kpi-sub">
          <t-tag v-for="r in runningTasks.slice(0, 3)" :key="r.id" theme="warning" size="small" style="margin: 2px">
            {{ r.task_type === 'backup' ? '备份' : r.task_type === 'migration' ? '迁移' : '恢复' }} #{{ r.id }}
          </t-tag>
          <span v-if="runningTasks.length === 0">无</span>
        </div>
      </div>
    </div>

    <!-- Recent Tasks -->
    <div class="ds-card" style="margin-top: 20px">
      <div class="ds-card-header">
        <h3 class="ds-card-title">
          <t-icon name="time" />
          最近任务
        </h3>
        <t-space>
          <t-button variant="text" theme="primary" @click="refresh">刷新</t-button>
        </t-space>
      </div>
      <div class="ds-table-wrap">
        <t-table
          :data="recentTasks"
          :columns="columns"
          row-key="id"
          hover
          stripe
          :loading="loading"
        >
          <template #task_type="{ row }">
            <t-tag :color="getTaskTypeColor(row.task_type)" size="small">
              {{ getTaskTypeLabel(row.task_type) }}
            </t-tag>
          </template>
          <template #status="{ row }">
            <t-tag :theme="getStatusTheme(row.status)" size="small">
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
            <t-button variant="text" theme="primary" size="small" @click="goToDetail(row)">
              详情
            </t-button>
          </template>
        </t-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";
import { fmtDatetime } from "../utils/format";

const router = useRouter();
const loading = ref(true);
const stats = ref({ datasources: 0, backupTasks: 0, migrationTasks: 0 });
const backupRecords = ref<any[]>([]);
const migrationRecords = ref<any[]>([]);
const restoreRecords = ref<any[]>([]);

const columns = [
  { colKey: "id", title: "ID", width: 80 },
  { colKey: "task_type", title: "类型", width: 90 },
  { colKey: "task_name", title: "任务名称", width: 180 },
  { colKey: "status", title: "状态", width: 100 },
  { colKey: "started_at", title: "开始时间", width: 160 },
  { colKey: "finished_at", title: "完成时间", width: 160 },
  { colKey: "duration", title: "耗时", width: 100 },
  { colKey: "action", title: "操作", width: 80 },
];

const recentTasks = computed(() => {
  const tasks = [
    ...backupRecords.value.map((r) => ({
      ...r,
      task_type: "backup" as const,
      task_name: r.task?.name || `备份任务 #${r.task_id}`,
    })),
    ...migrationRecords.value.map((r) => ({
      ...r,
      task_type: "migration" as const,
      task_name: r.task?.name || `迁移任务 #${r.task_id}`,
    })),
    ...restoreRecords.value.map((r) => ({
      ...r,
      task_type: "restore" as const,
      task_name: r.backup_name || `恢复 #${r.id}`,
    })),
  ];
  
  // Sort by started_at descending
  tasks.sort((a, b) => {
    const aTime = a.started_at ? new Date(a.started_at).getTime() : 0;
    const bTime = b.started_at ? new Date(b.started_at).getTime() : 0;
    return bTime - aTime;
  });
  
  return tasks.slice(0, 20);
});

const runningTasks = computed(() => recentTasks.value.filter((t) => t.status === "running"));

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

function getTaskTypeColor(type: string) {
  switch (type) {
    case "backup": return "#6366F1";
    case "migration": return "#10B981";
    case "restore": return "#F59E0B";
    default: return "#6B7280";
  }
}

function getTaskTypeLabel(type: string) {
  switch (type) {
    case "backup": return "备份";
    case "migration": return "迁移";
    case "restore": return "恢复";
    default: return type;
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

function goToDetail(row: any) {
  switch (row.task_type) {
    case "backup":
      router.push(`/backup/${row.task_id}/record/${row.id}`);
      break;
    case "migration":
      router.push(`/migration/${row.task_id}`);
      break;
    case "restore":
      router.push(`/logs`);
      break;
  }
}

async function fetchData() {
  loading.value = true;
  try {
    const [ds, backupTasks, migrationTasks, backups, migrations, restores] = await Promise.all([
      api.listDatasources(),
      api.listBackupTasks(),
      api.listMigrationTasks(),
      api.listBackupRecords(),
      api.listMigrationRecords(),
      api.listRestoreRecords({ limit: 20 }),
    ]);
    
    stats.value = {
      datasources: ds.length,
      backupTasks: backupTasks.length,
      migrationTasks: migrationTasks.length,
    };
    
    // Enrich backup records with task names
    const backupTaskMap = new Map(backupTasks.map((t: any) => [t.id, t]));
    backupRecords.value = backups.map((r: any) => ({
      ...r,
      task: backupTaskMap.get(r.task_id),
    }));
    
    // Enrich migration records with task names
    const migrationTaskMap = new Map(migrationTasks.map((t: any) => [t.id, t]));
    migrationRecords.value = migrations.map((r: any) => ({
      ...r,
      task: migrationTaskMap.get(r.task_id),
    }));
    
    restoreRecords.value = restores.items || restores || [];
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    loading.value = false;
  }
}

function refresh() {
  fetchData();
}

onMounted(() => {
  fetchData();
});
</script>
