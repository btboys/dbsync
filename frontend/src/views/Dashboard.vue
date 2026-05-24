<template>
  <div>
    <h2>仪表盘</h2>
    <t-row :gutter="16">
      <t-col :span="6">
        <t-card title="数据源" :loading="loading">
          <div class="stat-number">{{ stats.datasources }}</div>
        </t-card>
      </t-col>
      <t-col :span="6">
        <t-card title="备份任务" :loading="loading">
          <div class="stat-number">{{ stats.backupTasks }}</div>
        </t-card>
      </t-col>
      <t-col :span="6">
        <t-card title="迁移任务" :loading="loading">
          <div class="stat-number">{{ stats.migrationTasks }}</div>
        </t-card>
      </t-col>
      <t-col :span="6">
        <t-card title="最近备份" :loading="loading">
          <t-tag v-for="r in recentBackups" :key="r.id" :theme="r.status === 'success' ? 'success' : 'danger'" style="margin: 4px">
            {{ r.status }}
          </t-tag>
          <div v-if="recentBackups.length === 0">暂无</div>
        </t-card>
      </t-col>
    </t-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api } from "../api/client";

const loading = ref(true);
const stats = ref({ datasources: 0, backupTasks: 0, migrationTasks: 0 });
const recentBackups = ref<any[]>([]);

onMounted(async () => {
  try {
    const [ds, bt, mt, br] = await Promise.all([
      api.listDatasources(),
      api.listBackupTasks(),
      api.listMigrationTasks(),
      api.listBackupRecords(),
    ]);
    stats.value = {
      datasources: ds.length,
      backupTasks: bt.length,
      migrationTasks: mt.length,
    };
    recentBackups.value = br.slice(0, 5);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.stat-number {
  font-size: 36px;
  font-weight: bold;
  color: #0052d9;
  text-align: center;
  padding: 16px;
}
</style>
