<template>
  <div>
    <div class="ds-toolbar">
      <h2 class="ds-page-title" style="margin:0">
        <t-icon name="backup" class="ds-page-title-icon" />
        备份任务
      </h2>
      <t-button theme="primary" @click="$router.push('/backup/create')">
        <template #icon><t-icon name="add" /></template>
        新建任务
      </t-button>
    </div>

    <div class="ds-card">
      <div class="ds-table-wrap">
        <t-table :data="backupStore.tasks.map((t: any) => ({ ...t, record_count: recordCounts[t.id] || 0 }))" :columns="columns" row-key="id" :loading="backupStore.loading" hover stripe>
          <template #backup_type="{ row }">
            <t-tag :color="row.backup_type === 'full' ? '#6366F1' : '#10B981'">{{ row.backup_type === 'full' ? '全量' : '增量' }}</t-tag>
          </template>
          <template #is_enabled="{ row }">
            <t-switch :value="row.is_enabled" size="small" @change="(val: boolean) => handleToggle(row, val)" />
          </template>
          <template #record_count="{ row }">
            <t-button variant="text" @click="$router.push(`/backup/${row.id}`)">
              {{ row.record_count || 0 }} 条
            </t-button>
          </template>
          <template #action="{ row }">
            <t-space>
              <t-button variant="text" theme="primary" @click="$router.push(`/backup/${row.id}`)">详情</t-button>
              <t-button variant="text" @click="$router.push(`/backup/${row.id}/edit`)">编辑</t-button>
              <t-button variant="text" @click="handleRun(row)">执行</t-button>
              <t-button variant="text" theme="danger" @click="handleDelete(row)">删除</t-button>
            </t-space>
          </template>
        </t-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { useBackupStore } from "../stores";
import { api } from "../api/client";

const router = useRouter();

const backupStore = useBackupStore();
const recordCounts = ref<Record<number, number>>({});

const columns = [
  { colKey: "name", title: "名称", width: 200 },
  { colKey: "backup_type", title: "类型", width: 80 },
  { colKey: "retention_days", title: "保留天数", width: 100 },
  { colKey: "compression", title: "压缩", width: 80 },
  { colKey: "is_enabled", title: "启用", width: 80 },
  { colKey: "record_count", title: "备份记录", width: 100 },
  { colKey: "action", title: "操作", width: 200 },
];

onMounted(async () => {
  await backupStore.fetchTasks();
  await fetchRecordCounts();
});

async function fetchRecordCounts() {
  try {
    const records = await api.listBackupRecords();
    const counts: Record<number, number> = {};
    records.forEach((r: any) => {
      counts[r.task_id] = (counts[r.task_id] || 0) + 1;
    });
    recordCounts.value = counts;
  } catch {
    // ignore
  }
}

async function handleRun(row: any) {
  try {
    await backupStore.runTask(row.id);
    MessagePlugin.success("备份任务已触发");
    // 跳转到备份任务详情页
    router.push(`/backup/${row.id}`);
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

async function handleDelete(row: any) {
  try {
    await backupStore.deleteTask(row.id);
    MessagePlugin.success("已删除");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

async function handleToggle(row: any, val: boolean) {
  try {
    await backupStore.toggleTask(row.id, val);
    MessagePlugin.success(val ? "已启用" : "已禁用");
    row.is_enabled = val;
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}
</script>
