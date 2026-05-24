<template>
  <div>
    <t-card>
      <t-row justify="space-between" style="margin-bottom: 16px">
        <h2>数据源管理</h2>
        <t-button theme="primary" @click="showCreate = true">新增数据源</t-button>
      </t-row>

      <t-table :data="datasources" :columns="columns" row-key="id" :loading="loading">
        <template #type="{ row }">
          <t-tag>{{ row.type }}</t-tag>
        </template>
        <template #is_active="{ row }">
          <t-switch :value="row.is_active" disabled size="small" />
        </template>
        <template #action="{ row }">
          <t-space>
            <t-button variant="text" @click="$router.push(`/datasources/${row.id}`)">详情</t-button>
            <t-button variant="text" theme="danger" @click="handleDelete(row)">删除</t-button>
          </t-space>
        </template>
      </t-table>
    </t-card>

    <t-dialog v-model:visible="showCreate" header="新增数据源" @confirm="handleCreate" :confirm-btn="{ loading: creating }">
      <t-form ref="formRef" :data="form">
        <t-form-item label="名称" name="name" :rules="[{ required: true }]">
          <t-input v-model="form.name" />
        </t-form-item>
        <t-form-item label="类型" name="type" :rules="[{ required: true }]">
          <t-select v-model="form.type" :options="[
            { label: 'MySQL', value: 'mysql' },
            { label: 'PostgreSQL', value: 'postgresql' },
          ]" />
        </t-form-item>
        <t-form-item label="主机" name="host" :rules="[{ required: true }]">
          <t-input v-model="form.host" />
        </t-form-item>
        <t-form-item label="端口" name="port" :rules="[{ required: true }]">
          <t-input-number v-model="form.port" :min="1" :max="65535" />
        </t-form-item>
        <t-form-item label="用户名" name="username" :rules="[{ required: true }]">
          <t-input v-model="form.username" />
        </t-form-item>
        <t-form-item label="密码" name="password" :rules="[{ required: true }]">
          <t-input v-model="form.password" type="password" />
        </t-form-item>
        <t-form-item label="数据库" name="database" :rules="[{ required: true }]">
          <t-input v-model="form.database" />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";

const datasources = ref<any[]>([]);
const loading = ref(false);
const showCreate = ref(false);
const creating = ref(false);
const form = ref({
  name: "", type: "mysql", host: "localhost", port: 3306,
  username: "root", password: "", database: "",
});

const columns = [
  { colKey: "name", title: "名称" },
  { colKey: "type", title: "类型" },
  { colKey: "host", title: "主机" },
  { colKey: "port", title: "端口" },
  { colKey: "database", title: "数据库" },
  { colKey: "is_active", title: "状态" },
  { colKey: "action", title: "操作" },
];

onMounted(async () => {
  loading.value = true;
  datasources.value = await api.listDatasources();
  loading.value = false;
});

async function handleCreate() {
  creating.value = true;
  try {
    await api.createDatasource(form.value);
    MessagePlugin.success("创建成功");
    showCreate.value = false;
    datasources.value = await api.listDatasources();
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    creating.value = false;
  }
}

async function handleDelete(row: any) {
  await api.deleteDatasource(row.id);
  MessagePlugin.success("已删除");
  datasources.value = await api.listDatasources();
}
</script>
