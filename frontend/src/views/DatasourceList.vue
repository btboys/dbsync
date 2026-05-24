<template>
  <div>
    <div class="ds-toolbar">
      <h2 class="ds-page-title" style="margin:0">
        <t-icon name="server" class="ds-page-title-icon" />
        数据源管理
      </h2>
      <t-button theme="primary" @click="showCreate = true">
        <template #icon><t-icon name="add" /></template>
        新增数据源
      </t-button>
    </div>

    <div class="ds-card">
      <div class="ds-table-wrap">
        <t-table :data="dsStore.datasources" :columns="columns" row-key="id" :loading="dsStore.loading" hover stripe>
          <template #type="{ row }">
            <t-tag :color="row.type === 'mysql' ? '#F29100' : '#0052D9'">{{ row.type }}</t-tag>
          </template>
          <template #is_active="{ row }">
            <t-switch v-model="row.is_active" size="small" @change="(val: boolean) => handleToggle(row, val)" />
          </template>
          <template #action="{ row }">
            <t-space>
              <t-button variant="text" theme="primary" @click="openEdit(row)">编辑</t-button>
              <t-button variant="text" theme="primary" @click="$router.push(`/datasources/${row.id}`)">详情</t-button>
              <t-button variant="text" theme="danger" @click="handleDelete(row)">删除</t-button>
            </t-space>
          </template>
        </t-table>
      </div>
    </div>

    <!-- Create Dialog -->
    <t-dialog v-model:visible="showCreate" header="新增数据源" @confirm="handleCreate" :confirm-btn="{ loading: creating }" width="520px">
      <t-form ref="formRef" :data="form">
        <t-form-item label="名称" name="name" :rules="[{ required: true }]">
          <t-input v-model="form.name" placeholder="如: 生产数据库" />
        </t-form-item>
        <t-form-item label="类型" name="type" :rules="[{ required: true }]">
          <t-select v-model="form.type" :options="[
            { label: 'MySQL', value: 'mysql' },
            { label: 'PostgreSQL', value: 'postgresql' },
          ]" />
        </t-form-item>
        <t-form-item label="主机" name="host" :rules="[{ required: true }]">
          <t-input v-model="form.host" placeholder="localhost" />
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

    <!-- Edit Dialog -->
    <t-dialog v-model:visible="showEdit" header="编辑数据源" @confirm="handleEdit" :confirm-btn="{ loading: editing }" width="520px">
      <t-form ref="editFormRef" :data="editForm">
        <t-form-item label="名称" name="name" :rules="[{ required: true }]">
          <t-input v-model="editForm.name" placeholder="如: 生产数据库" />
        </t-form-item>
        <t-form-item label="类型" name="type" :rules="[{ required: true }]">
          <t-select v-model="editForm.type" :options="[
            { label: 'MySQL', value: 'mysql' },
            { label: 'PostgreSQL', value: 'postgresql' },
          ]" />
        </t-form-item>
        <t-form-item label="主机" name="host" :rules="[{ required: true }]">
          <t-input v-model="editForm.host" placeholder="localhost" />
        </t-form-item>
        <t-form-item label="端口" name="port" :rules="[{ required: true }]">
          <t-input-number v-model="editForm.port" :min="1" :max="65535" />
        </t-form-item>
        <t-form-item label="用户名" name="username" :rules="[{ required: true }]">
          <t-input v-model="editForm.username" />
        </t-form-item>
        <t-form-item label="密码" name="password">
          <t-input v-model="editForm.password" type="password" placeholder="不填表示不修改密码" />
        </t-form-item>
        <t-form-item label="数据库" name="database" :rules="[{ required: true }]">
          <t-input v-model="editForm.database" />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { MessagePlugin } from "tdesign-vue-next";
import { useDatasourceStore } from "../stores";

const loading = ref(false);
const showCreate = ref(false);
const showEdit = ref(false);
const creating = ref(false);
const editing = ref(false);
const editingId = ref<number | null>(null);

const form = ref({
  name: "", type: "mysql", host: "localhost", port: 3306,
  username: "root", password: "", database: "",
});

const editForm = ref({
  name: "", type: "mysql", host: "", port: 3306,
  username: "", password: "", database: "",
});

const dsStore = useDatasourceStore();

const columns = [
  { colKey: "name", title: "名称", width: 160 },
  { colKey: "type", title: "类型", width: 100 },
  { colKey: "host", title: "主机" },
  { colKey: "port", title: "端口", width: 80 },
  { colKey: "database", title: "数据库" },
  { colKey: "is_active", title: "状态", width: 80 },
  { colKey: "action", title: "操作", width: 200 },
];

onMounted(async () => {
  loading.value = true;
  await dsStore.fetchDatasources();
  loading.value = false;
});

async function handleCreate() {
  creating.value = true;
  try {
    await dsStore.createDatasource(form.value);
    MessagePlugin.success("创建成功");
    showCreate.value = false;
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    creating.value = false;
  }
}

function openEdit(row: any) {
  editingId.value = row.id;
  editForm.value = {
    name: row.name,
    type: row.type,
    host: row.host,
    port: row.port,
    username: row.username,
    password: row.password,
    database: row.database,
  };
  showEdit.value = true;
}

async function handleEdit() {
  if (!editingId.value) return;
  editing.value = true;
  try {
    const data: any = {
      name: editForm.value.name,
      type: editForm.value.type,
      host: editForm.value.host,
      port: editForm.value.port,
      username: editForm.value.username,
      database: editForm.value.database,
    };
    // Only include password if user entered a new one
    if (editForm.value.password) {
      data.password = editForm.value.password;
    }
    
    await dsStore.updateDatasource(editingId.value, data);
    MessagePlugin.success("更新成功");
    showEdit.value = false;
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    editing.value = false;
  }
}

async function handleToggle(row: any, val: boolean) {
  try {
    await dsStore.updateDatasource(row.id, { is_active: val });
    MessagePlugin.success(val ? "已启用" : "已禁用");
  } catch (e: any) {
    MessagePlugin.error(e.message);
    // Revert on error
    row.is_active = !val;
  }
}

async function handleDelete(row: any) {
  try {
    await dsStore.deleteDatasource(row.id);
    MessagePlugin.success("已删除");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}
</script>
