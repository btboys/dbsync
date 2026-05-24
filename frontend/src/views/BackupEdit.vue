<template>
  <div v-if="task">
    <div class="ds-toolbar">
      <h2 class="ds-page-title" style="margin:0">
        <t-icon name="backup" class="ds-page-title-icon" />
        编辑备份任务
      </h2>
    </div>
    <div class="ds-card" style="max-width: 640px;">
      <t-form :data="form" @submit="handleSubmit">
        <t-form-item label="名称" name="name" :rules="[{ required: true }]">
          <t-input v-model="form.name" placeholder="如: 每日全量备份" />
        </t-form-item>
        <t-form-item label="数据源" name="datasource_id" :rules="[{ required: true }]">
          <t-select v-model="form.datasource_id" :options="datasources.map((d: any) => ({ label: d.name, value: d.id }))" />
        </t-form-item>
        <t-form-item label="备份类型" name="backup_type">
          <t-radio-group v-model="form.backup_type">
            <t-radio value="full">全量</t-radio>
            <t-radio value="incremental">增量</t-radio>
          </t-radio-group>
        </t-form-item>
        <t-form-item label="压缩" name="compression">
          <t-switch v-model="form.compression" />
        </t-form-item>
        <t-form-item label="保留天数" name="retention_days">
          <t-input-number v-model="form.retention_days" :min="1" />
        </t-form-item>
        <t-form-item label="定时策略" name="schedule_cron">
          <CronPicker v-model="scheduleCron" />
        </t-form-item>
        <t-form-item>
          <t-space>
            <t-button theme="primary" type="submit" :loading="submitting">
              <template #icon><t-icon name="check" /></template>
              保存
            </t-button>
            <t-button variant="outline" @click="$router.push('/backup')">取消</t-button>
          </t-space>
        </t-form-item>
      </t-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";
import CronPicker from "../components/CronPicker.vue";

const route = useRoute();
const router = useRouter();
const datasources = ref<any[]>([]);
const submitting = ref(false);
const task = ref<any>(null);
const scheduleCron = ref("");
const form = ref({
  name: "",
  datasource_id: null as number | null,
  backup_type: "full",
  compression: true,
  retention_days: 30,
  schedule_config: null as any,
});

onMounted(async () => {
  const id = Number(route.params.id);
  const [ds, t] = await Promise.all([
    api.listDatasources(),
    api.getBackupTask(id),
  ]);
  datasources.value = ds;
  task.value = t;
  
  form.value = {
    name: t.name,
    datasource_id: t.datasource_id,
    backup_type: t.backup_type,
    compression: t.compression,
    retention_days: t.retention_days,
    schedule_config: t.schedule_config,
  };
  scheduleCron.value = t.schedule_config?.cron || "";
});

async function handleSubmit() {
  submitting.value = true;
  try {
    form.value.schedule_config = scheduleCron.value ? { cron: scheduleCron.value } : null;
    await api.updateBackupTask(Number(route.params.id), form.value);
    MessagePlugin.success("保存成功");
    router.push("/backup");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    submitting.value = false;
  }
}
</script>
