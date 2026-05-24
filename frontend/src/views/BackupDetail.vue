<template>
  <t-card v-if="task" :title="task.name">
    <t-descriptions>
      <t-descriptions-item label="类型">{{ task.backup_type === 'full' ? '全量' : '增量' }}</t-descriptions-item>
      <t-descriptions-item label="压缩">{{ task.compression ? '是' : '否' }}</t-descriptions-item>
      <t-descriptions-item label="保留天数">{{ task.retention_days }}</t-descriptions-item>
    </t-descriptions>

    <t-divider />
    <t-row justify="space-between">
      <h3>执行记录</h3>
      <t-button @click="handleRun">立即执行</t-button>
    </t-row>
    <t-table :data="records" :columns="recordColumns" row-key="id">
      <template #status="{ row }">
        <t-tag :theme="row.status === 'success' ? 'success' : row.status === 'running' ? 'warning' : 'danger'">
          {{ row.status === 'running' ? '执行中' : row.status === 'success' ? '成功' : '失败' }}
        </t-tag>
      </template>
      <template #action="{ row }">
        <t-button variant="text" @click="$router.push(`/backup/${task.id}/record/${row.id}`)">详情</t-button>
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
  { colKey: "file_size", title: "大小" },
  { colKey: "started_at", title: "开始时间" },
  { colKey: "finished_at", title: "完成时间" },
  { colKey: "action", title: "操作" },
];

onMounted(async () => {
  const id = Number(route.params.id);
  task.value = await api.getBackupTask(id);
  records.value = await api.listBackupRecords(id);
});

async function handleRun() {
  await api.runBackupTask(task.value!.id);
  MessagePlugin.success("任务已触发");
  records.value = await api.listBackupRecords(task.value!.id);
}
</script>
