<template>
  <div>
    <t-card>
      <t-row justify="space-between" style="margin-bottom: 16px">
        <h2>备份任务</h2>
        <t-button theme="primary" @click="$router.push('/backup/create')">新建任务</t-button>
      </t-row>
      <t-table :data="tasks" :columns="columns" row-key="id" :loading="loading">
        <template #backup_type="{ row }">
          <t-tag>{{ row.backup_type === 'full' ? '全量' : '增量' }}</t-tag>
        </template>
        <template #is_enabled="{ row }">
          <t-switch :value="row.is_enabled" disabled size="small" />
        </template>
        <template #action="{ row }">
          <t-space>
            <t-button variant="text" @click="$router.push(`/backup/${row.id}`)">详情</t-button>
            <t-button variant="text" @click="handleRun(row)">执行</t-button>
            <t-button variant="text" theme="danger" @click="handleDelete(row)">删除</t-button>
          </t-space>
        </template>
      </t-table>
    </t-card>
  </div>
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
  { colKey: "retention_days", title: "保留天数" },
  { colKey: "compression", title: "压缩" },
  { colKey: "is_enabled", title: "启用" },
  { colKey: "action", title: "操作" },
];

onMounted(async () => {
  loading.value = true;
  tasks.value = await api.listBackupTasks();
  loading.value = false;
});

async function handleRun(row: any) {
  await api.runBackupTask(row.id);
  MessagePlugin.success("备份任务已触发");
}

async function handleDelete(row: any) {
  await api.deleteBackupTask(row.id);
  tasks.value = await api.listBackupTasks();
  MessagePlugin.success("已删除");
}
</script>
