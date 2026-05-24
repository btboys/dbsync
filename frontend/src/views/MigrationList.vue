<template>
  <div>
    <div class="ds-toolbar">
      <h2 class="ds-page-title" style="margin:0">
        <t-icon name="swap" class="ds-page-title-icon" />
        迁移任务
      </h2>
      <t-button theme="primary" @click="$router.push('/migration/create')">
        <template #icon><t-icon name="add" /></template>
        新建迁移
      </t-button>
    </div>

    <div class="ds-card">
      <div class="ds-table-wrap">
        <t-table :data="migrationStore.tasks" :columns="columns" row-key="id" :loading="migrationStore.loading" hover stripe>
          <template #transfer_type="{ row }">
            <t-tag :color="row.transfer_type === 'schema_and_data' ? '#6366F1' : row.transfer_type === 'data_only' ? '#10B981' : '#F59E0B'">
              {{ row.transfer_type === 'schema_only' ? '仅结构' : row.transfer_type === 'data_only' ? '仅数据' : '结构+数据' }}
            </t-tag>
          </template>
          <template #action="{ row }">
            <t-space>
              <t-button variant="text" theme="primary" @click="$router.push(`/migration/${row.id}`)">详情</t-button>
              <t-button variant="text" @click="$router.push(`/migration/${row.id}/edit`)">编辑</t-button>
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
import { onMounted } from "vue";
import { MessagePlugin } from "tdesign-vue-next";
import { useMigrationStore } from "../stores";

const migrationStore = useMigrationStore();

const columns = [
  { colKey: "name", title: "名称", width: 200 },
  { colKey: "transfer_type", title: "迁移类型", width: 120 },
  { colKey: "action", title: "操作", width: 280 },
];

onMounted(async () => {
  await migrationStore.fetchTasks();
});

async function handleRun(row: any) {
  try {
    await migrationStore.runTask(row.id);
    MessagePlugin.success("迁移任务已触发");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

async function handleDelete(row: any) {
  try {
    await migrationStore.deleteTask(row.id);
    MessagePlugin.success("已删除");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}
</script>
