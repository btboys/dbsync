<template>
  <div v-if="ds">
    <div class="ds-toolbar">
      <h2 class="ds-page-title" style="margin:0">
        <t-icon name="server" class="ds-page-title-icon" />
        {{ ds.name }}
      </h2>
      <t-space>
        <t-button theme="primary" @click="showEditDialog">
          <template #icon><t-icon name="edit" /></template>
          编辑
        </t-button>
        <t-button @click="handleTest">
          <template #icon><t-icon name="check-circle" /></template>
          测试连接
        </t-button>
        <t-button variant="outline" @click="$router.push('/datasources')">返回</t-button>
      </t-space>
    </div>

    <div class="ds-card">
      <div style="display: flex; flex-direction: column; gap: 16px;">
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">ID</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 14px;">{{ ds.id }}</div>
        </div>

        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">名称</div>
          <div style="font-size: 14px; font-weight: 500;">{{ ds.name }}</div>
        </div>

        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">类型</div>
          <t-tag :color="ds.type === 'mysql' ? '#F29100' : '#0052D9'">{{ ds.type }}</t-tag>
        </div>

        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">主机地址</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 14px;">{{ ds.host }}</div>
        </div>

        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">端口</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 14px;">{{ ds.port }}</div>
        </div>

        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">用户名</div>
          <div style="font-size: 14px;">{{ ds.username }}</div>
        </div>

        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">数据库</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 14px;">{{ ds.database }}</div>
        </div>

        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">状态</div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <t-switch v-model="ds.is_active" size="small" @change="handleToggleActive" />
            <t-tag :theme="ds.is_active ? 'success' : 'default'" size="small">{{ ds.is_active ? '启用' : '禁用' }}</t-tag>
          </div>
        </div>

        <div v-if="ds.ssl_config">
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">SSL 配置</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 13px;">{{ JSON.stringify(ds.ssl_config, null, 2) }}</div>
        </div>

        <div v-if="ds.extra_params">
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">额外参数</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 13px;">{{ JSON.stringify(ds.extra_params, null, 2) }}</div>
        </div>

        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">创建时间</div>
          <div style="font-size: 14px;">{{ fmtDatetime(ds.created_at) }}</div>
        </div>

        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">更新时间</div>
          <div style="font-size: 14px;">{{ fmtDatetime(ds.updated_at) }}</div>
        </div>
      </div>
    </div>

    <!-- Edit Dialog -->
    <t-dialog
      v-model:visible="showEdit"
      header="编辑数据源"
      @confirm="handleEdit"
      :confirm-btn="{ loading: editing }"
      width="520px"
    >
      <t-form ref="formRef" :data="editForm">
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
import { useRoute } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";
import { fmtDatetime } from "../utils/format";
import { useDatasourceStore } from "../stores";

const route = useRoute();
const dsStore = useDatasourceStore();
const ds = ref<any>(null);
const showEdit = ref(false);
const editing = ref(false);
const editForm = ref({
  name: "",
  type: "mysql",
  host: "",
  port: 3306,
  username: "",
  password: "",
  database: "",
});

onMounted(async () => {
  ds.value = await api.getDatasource(Number(route.params.id));
});

async function handleTest() {
  try {
    await api.testDatasource(ds.value.id);
    MessagePlugin.success("连接成功");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}

async function handleToggleActive(val: boolean) {
  try {
    await dsStore.updateDatasource(ds.value.id, { is_active: val });
    MessagePlugin.success(val ? "已启用" : "已禁用");
  } catch (e: any) {
    MessagePlugin.error(e.message);
    ds.value.is_active = !val;
  }
}

function showEditDialog() {
  editForm.value = {
    name: ds.value.name,
    type: ds.value.type,
    host: ds.value.host,
    port: ds.value.port,
    username: ds.value.username,
    password: "",
    database: ds.value.database,
  };
  showEdit.value = true;
}

async function handleEdit() {
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
    
    await dsStore.updateDatasource(ds.value.id, data);
    MessagePlugin.success("更新成功");
    showEdit.value = false;
    ds.value = await api.getDatasource(Number(route.params.id));
  } catch (e: any) {
    MessagePlugin.error(e.message);
  } finally {
    editing.value = false;
  }
}
</script>
