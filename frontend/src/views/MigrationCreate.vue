<template>
  <t-card title="新建迁移任务">
    <t-form :data="form" style="max-width: 600px" @submit="handleSubmit">
      <t-form-item label="名称" name="name" :rules="[{ required: true }]">
        <t-input v-model="form.name" />
      </t-form-item>
      <t-form-item label="源数据源" name="source_datasource_id" :rules="[{ required: true }]">
        <t-select v-model="form.source_datasource_id" :options="datasources.map((d: any) => ({ label: `${d.name} (${d.type})`, value: d.id }))" />
      </t-form-item>
      <t-form-item label="目标数据源" name="target_datasource_id" :rules="[{ required: true }]">
        <t-select v-model="form.target_datasource_id" :options="datasources.map((d: any) => ({ label: `${d.name} (${d.type})`, value: d.id }))" />
      </t-form-item>
      <t-form-item label="迁移内容" name="transfer_type">
        <t-radio-group v-model="form.transfer_type">
          <t-radio value="schema_only">仅结构</t-radio>
          <t-radio value="data_only" checked>仅数据</t-radio>
          <t-radio value="schema_and_data">结构+数据</t-radio>
        </t-radio-group>
      </t-form-item>
      <t-form-item label="包含表" name="table_include">
        <t-input v-model="includeStr" placeholder="留空为全部，逗号分隔" />
      </t-form-item>
      <t-form-item label="排除表" name="table_exclude">
        <t-input v-model="excludeStr" placeholder="逗号分隔" />
      </t-form-item>
      <t-form-item>
        <t-space>
          <t-button theme="primary" type="submit" :loading="submitting">创建</t-button>
          <t-button variant="outline" @click="$router.push('/migration')">取消</t-button>
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
const includeStr = ref("");
const excludeStr = ref("");
const form = ref({
  name: "", source_datasource_id: null as number | null,
  target_datasource_id: null as number | null,
  transfer_type: "data_only", table_include: null as string[] | null,
  table_exclude: null as string[] | null,
});

onMounted(async () => {
  datasources.value = await api.listDatasources();
});

async function handleSubmit() {
  submitting.value = true;
  try {
    form.value.table_include = includeStr.value
      ? includeStr.value.split(",").map((s) => s.trim())
      : null;
    form.value.table_exclude = excludeStr.value
      ? excludeStr.value.split(",").map((s) => s.trim())
      : null;
    await api.createMigrationTask(form.value);
    MessagePlugin.success("创建成功");
    router.push("/migration");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    submitting.value = false;
  }
}
</script>
