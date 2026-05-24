<template>
  <t-card v-if="task" :title="task.name">
    <t-descriptions>
      <t-descriptions-item label="迁移类型">{{ task.transfer_type }}</t-descriptions-item>
    </t-descriptions>

    <t-divider />
    <t-row justify="space-between">
      <h3>执行记录</h3>
      <t-button @click="handleRun">执行迁移</t-button>
    </t-row>
    <t-table :data="records" :columns="recordColumns" row-key="id">
      <template #status="{ row }">
        <t-tag :theme="row.status === 'success' ? 'success' : row.status === 'running' ? 'warning' : 'danger'">
          {{ row.status }}
        </t-tag>
      </template>
    </t-table>
  </t-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";

const route = useRoute();
const task = ref<any>(null);
const records = ref<any[]>([]);
const recordColumns = [
  { colKey: "id", title: "ID" },
  { colKey: "status", title: "状态" },
  { colKey: "rows_transferred", title: "传输行数" },
  { colKey: "started_at", title: "开始时间" },
  { colKey: "finished_at", title: "完成时间" },
];

onMounted(async () => {
  const id = Number(route.params.id);
  task.value = await api.getMigrationTask(id);
  records.value = await api.listMigrationRecords(id);
});

async function handleRun() {
  await api.runMigrationTask(task.value!.id);
  MessagePlugin.success("迁移任务已触发");
  records.value = await api.listMigrationRecords(task.value!.id);
}
</script>
