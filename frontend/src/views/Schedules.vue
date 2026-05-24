<template>
  <t-card title="定时策略">
    <t-table :data="tasks" :columns="columns" row-key="id" :loading="loading">
      <template #backup_type="{ row }">
        <t-tag>{{ row.backup_type === 'full' ? '全量' : '增量' }}</t-tag>
      </template>
      <template #is_enabled="{ row }">
        <t-switch :value="row.is_enabled" @change="(v: any) => toggleEnabled(row, v)" size="small" />
      </template>
      <template #schedule_config="{ row }">
        {{ row.schedule_config?.cron || '手动' }}
      </template>
    </t-table>
  </t-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";

const tasks = ref<any[]>([]);
const loading = ref(false);
const columns = [
  { colKey: "name", title: "名称" },
  { colKey: "backup_type", title: "类型" },
  { colKey: "schedule_config", title: "Cron" },
  { colKey: "is_enabled", title: "启用" },
];

onMounted(async () => {
  loading.value = true;
  tasks.value = (await api.listBackupTasks()).filter((t: any) => t.schedule_config);
  loading.value = false;
});

async function toggleEnabled(row: any, val: boolean) {
  await api.updateBackupTask(row.id, { is_enabled: val });
  MessagePlugin.success(val ? "已启用" : "已禁用");
}
</script>
