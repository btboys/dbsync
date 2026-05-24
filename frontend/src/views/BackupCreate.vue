<template>
  <t-card title="新建备份任务">
    <t-form :data="form" style="max-width: 600px" @submit="handleSubmit">
      <t-form-item label="名称" name="name" :rules="[{ required: true }]">
        <t-input v-model="form.name" />
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
      <t-form-item label="定时策略(Cron)" name="schedule_cron">
        <t-input v-model="scheduleCron" placeholder="留空为手动触发，例: 0 2 * * *" />
      </t-form-item>
      <t-form-item>
        <t-space>
          <t-button theme="primary" type="submit" :loading="submitting">创建</t-button>
          <t-button variant="outline" @click="$router.push('/backup')">取消</t-button>
        </t-space>
      </t-form-item>
    </t-form>
  </t-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";

const router = useRouter();
const datasources = ref<any[]>([]);
const submitting = ref(false);
const scheduleCron = ref("");
const form = ref({
  name: "", datasource_id: null as number | null, backup_type: "full",
  compression: true, retention_days: 30, schedule_config: null as any,
});

onMounted(async () => {
  datasources.value = await api.listDatasources();
});

async function handleSubmit() {
  submitting.value = true;
  try {
    form.value.schedule_config = scheduleCron.value ? { cron: scheduleCron.value } : null;
    await api.createBackupTask(form.value);
    MessagePlugin.success("创建成功");
    router.push("/backup");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    submitting.value = false;
  }
}
</script>
