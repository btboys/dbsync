<template>
  <t-card>
    <t-row justify="space-between" style="margin-bottom: 16px">
      <h2>迁移任务</h2>
      <t-button theme="primary" @click="$router.push('/migration/create')">新建迁移</t-button>
    </t-row>
    <t-table :data="tasks" :columns="columns" row-key="id" :loading="loading">
      <template #transfer_type="{ row }">
        <t-tag>{{ row.transfer_type }}</t-tag>
      </template>
      <template #action="{ row }">
        <t-space>
          <t-button variant="text" @click="$router.push(`/migration/${row.id}`)">详情</t-button>
          <t-button variant="text" @click="handleRun(row)">执行</t-button>
          <t-button variant="text" theme="danger" @click="handleDelete(row)">删除</t-button>
        </t-space>
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
  { colKey: "transfer_type", title: "迁移类型" },
  { colKey: "action", title: "操作" },
];

onMounted(async () => {
  loading.value = true;
  tasks.value = await api.listMigrationTasks();
  loading.value = false;
});

async function handleRun(row: any) {
  await api.runMigrationTask(row.id);
  MessagePlugin.success("迁移任务已触发");
}

async function handleDelete(row: any) {
  await api.deleteMigrationTask(row.id);
  tasks.value = await api.listMigrationTasks();
  MessagePlugin.success("已删除");
}
</script>
