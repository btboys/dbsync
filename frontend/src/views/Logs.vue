<template>
  <t-card title="任务日志">
    <t-table :data="logs" :columns="columns" row-key="id" :loading="loading">
      <template #level="{ row }">
        <t-tag :theme="row.level === 'error' ? 'danger' : row.level === 'warning' ? 'warning' : 'default'">
          {{ row.level }}
        </t-tag>
      </template>
    </t-table>
  </t-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api } from "../api/client";

const logs = ref<any[]>([]);
const loading = ref(false);
const columns = [
  { colKey: "id", title: "ID" },
  { colKey: "task_type", title: "任务类型" },
  { colKey: "level", title: "级别" },
  { colKey: "message", title: "消息" },
  { colKey: "created_at", title: "时间" },
];

onMounted(async () => {
  loading.value = true;
  logs.value = [];
  loading.value = false;
});
</script>
