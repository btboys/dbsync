<template>
  <div>
    <div class="ds-toolbar">
      <t-button variant="text" @click="$router.back()">
        <template #icon><t-icon name="chevron-left" /></template>
        返回
      </t-button>
      <h2 class="ds-page-title" style="margin:0">
        <t-icon name="file" class="ds-page-title-icon" />
        过程日志详情
      </h2>
    </div>

    <div class="ds-card">
      <div class="ds-card-header">
        <h3 class="ds-card-title">
          <t-icon name="file" />
          过程日志
          <span v-if="taskInfo" style="margin-left: 12px; font-size: 14px; color: var(--ds-text-secondary); font-weight: normal;">
            {{ taskInfo.type === 'backup' ? '备份' : '迁移' }} #{{ taskInfo.recordId }}
          </span>
        </h3>
      </div>
      <div class="ds-table-wrap">
        <t-table
          :data="logs"
          :columns="columns"
          row-key="id"
          :pagination="pagination"
          @page-change="onPageChange"
          hover
          stripe
        >
          <template #level="{ row }">
            <t-tag :theme="row.level === 'error' ? 'danger' : row.level === 'warning' ? 'warning' : 'default'">
              {{ row.level }}
            </t-tag>
          </template>
          <template #created_at="{ row }">
            {{ fmtDatetime(row.created_at) }}
          </template>
        </t-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { api } from "../api/client";
import { MessagePlugin } from "tdesign-vue-next";
import { fmtDatetime } from "../utils/format";

const route = useRoute();
const logs = ref<any[]>([]);
const taskInfo = ref<any>(null);
const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
});

const columns = [
  { colKey: "id", title: "ID", width: 80 },
  { colKey: "level", title: "级别", width: 80 },
  { colKey: "message", title: "消息" },
  { colKey: "created_at", title: "时间", width: 180 },
];

async function loadLogs() {
  try {
    const taskType = route.query.task_type as string;
    const taskRecordId = Number(route.query.task_record_id);
    
    if (!taskType || !taskRecordId) {
      MessagePlugin.error("缺少必要的参数");
      return;
    }
    
    taskInfo.value = { type: taskType, recordId: taskRecordId };
    
    const offset = (pagination.value.current - 1) * pagination.value.pageSize;
    const res = await api.listTaskProcessLogs({
      task_type: taskType,
      task_record_id: taskRecordId,
      limit: pagination.value.pageSize,
      offset: offset,
    });
    logs.value = res.items;
    pagination.value.total = res.total;
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

function onPageChange(pageInfo: any) {
  pagination.value.current = pageInfo.current;
  pagination.value.pageSize = pageInfo.pageSize;
  loadLogs();
}

onMounted(() => {
  loadLogs();
});
</script>

<style scoped>
.ds-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
</style>
