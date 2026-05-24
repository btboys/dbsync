<template>
  <div>
    <div class="ds-toolbar">
      <h2 class="ds-page-title" style="margin:0">
        <t-icon name="time" class="ds-page-title-icon" />
        定时策略
      </h2>
      <t-button theme="primary" @click="showDialog = true">
        <template #icon><t-icon name="add" /></template>
        新建定时策略
      </t-button>
    </div>

    <div class="ds-card">
      <div class="ds-table-wrap">
        <t-table :data="backupStore.scheduledTasks" :columns="columns" row-key="id" :loading="backupStore.loading" hover stripe>
          <template #backup_type="{ row }">
            <t-tag :color="row.backup_type === 'full' ? '#6366F1' : '#10B981'">{{ row.backup_type === 'full' ? '全量' : '增量' }}</t-tag>
          </template>
          <template #is_enabled="{ row }">
            <t-switch :value="row.is_enabled" @change="(v: any) => toggleEnabled(row, v)" size="small" />
          </template>
          <template #schedule_config="{ row }">
            <code style="font-family: 'Fira Code', monospace; font-size: 13px; background: var(--ds-bg); padding: 2px 6px; border-radius: 4px;">{{ row.schedule_config?.cron || '手动' }}</code>
          </template>
          <template #action="{ row }">
            <t-space>
              <t-button variant="text" theme="primary" @click="openEdit(row)">编辑</t-button>
              <t-button variant="text" theme="danger" @click="handleDelete(row)">删除</t-button>
            </t-space>
          </template>
        </t-table>
      </div>
    </div>

    <t-dialog v-model:visible="showDialog" :header="editingId ? '编辑定时策略' : '新建定时策略'" @confirm="handleSubmit" @close="resetForm" width="520px">
      <t-form :data="form">
        <t-form-item label="名称" name="name">
          <t-input v-model="form.name" />
        </t-form-item>
        <t-form-item label="数据源" name="datasource_id">
          <t-select v-model="form.datasource_id" :options="dsStore.datasources.map((d: any) => ({ label: `${d.name} (${d.type})`, value: d.id }))" />
        </t-form-item>
        <t-form-item label="备份类型" name="backup_type">
          <t-radio-group v-model="form.backup_type">
            <t-radio value="full">全量</t-radio>
            <t-radio value="incremental">增量</t-radio>
          </t-radio-group>
        </t-form-item>
        <t-form-item label="定时策略" name="cron">
          <CronPicker v-model="cronExpr" />
        </t-form-item>
        <t-form-item label="启用" name="is_enabled">
          <t-switch v-model="form.is_enabled" />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { MessagePlugin } from "tdesign-vue-next";
import { useBackupStore, useDatasourceStore } from "../stores";
import CronPicker from "../components/CronPicker.vue";

const backupStore = useBackupStore();
const dsStore = useDatasourceStore();

const showDialog = ref(false);
const editingId = ref<number | null>(null);
const cronExpr = ref("");
const form = ref({
  name: "",
  datasource_id: null as number | null,
  backup_type: "full",
  schedule_config: null as any,
  is_enabled: true,
});

const columns = [
  { colKey: "name", title: "名称" },
  { colKey: "backup_type", title: "类型", width: 80 },
  { colKey: "schedule_config", title: "Cron", width: 140 },
  { colKey: "is_enabled", title: "启用", width: 80 },
  { colKey: "action", title: "操作", width: 150 },
];

onMounted(async () => {
  await Promise.all([backupStore.fetchTasks(), dsStore.fetchDatasources()]);
});

async function toggleEnabled(row: any, val: boolean) {
  try {
    await backupStore.updateTask(row.id, { is_enabled: val });
    MessagePlugin.success(val ? "已启用" : "已禁用");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

function openEdit(row: any) {
  editingId.value = row.id;
  form.value = {
    name: row.name,
    datasource_id: row.datasource_id,
    backup_type: row.backup_type,
    schedule_config: row.schedule_config,
    is_enabled: row.is_enabled,
  };
  cronExpr.value = row.schedule_config?.cron || "";
  showDialog.value = true;
}

function resetForm() {
  editingId.value = null;
  form.value = {
    name: "",
    datasource_id: null,
    backup_type: "full",
    schedule_config: null,
    is_enabled: true,
  };
  cronExpr.value = "";
}

async function handleSubmit() {
  try {
    form.value.schedule_config = cronExpr.value ? { cron: cronExpr.value } : null;
    if (editingId.value) {
      await backupStore.updateTask(editingId.value, form.value);
      MessagePlugin.success("保存成功");
    } else {
      await backupStore.createTask(form.value);
      MessagePlugin.success("创建成功");
    }
    showDialog.value = false;
    resetForm();
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

async function handleDelete(row: any) {
  try {
    await backupStore.deleteTask(row.id);
    MessagePlugin.success("已删除");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}
</script>
