<template>
  <t-card title="恢复管理">
    <t-table :data="records" :columns="columns" row-key="id" :loading="loading">
      <template #status="{ row }">
        <t-tag :theme="row.status === 'success' ? 'success' : 'danger'">{{ row.status }}</t-tag>
      </template>
      <template #action="{ row }">
        <t-button v-if="row.status === 'success'" variant="text" @click="handleRestore(row)">恢复</t-button>
      </template>
    </t-table>
  </t-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";

const records = ref<any[]>([]);
const loading = ref(false);
const columns = [
  { colKey: "id", title: "ID" },
  { colKey: "status", title: "状态" },
  { colKey: "file_path", title: "文件" },
  { colKey: "started_at", title: "时间" },
  { colKey: "action", title: "操作" },
];

onMounted(async () => {
  loading.value = true;
  records.value = await api.listBackupRecords();
  loading.value = false;
});

async function handleRestore(row: any) {
  await api.restoreBackup(row.id);
  MessagePlugin.success("恢复任务已触发");
}
</script>
