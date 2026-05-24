<template>
  <div v-if="record">
    <div class="ds-toolbar">
      <h2 class="ds-page-title" style="margin:0">
        <t-icon name="file" class="ds-page-title-icon" />
        备份记录详情
      </h2>
      <t-space>
        <t-button v-if="record.status === 'success'" @click="showRestoreDialog">
          <template #icon><t-icon name="rollback" /></template>
          恢复到此备份
        </t-button>
        <t-button variant="outline" theme="danger" @click="handleDelete">
          <template #icon><t-icon name="delete" /></template>
          删除
        </t-button>
        <t-button variant="outline" @click="$router.back()">返回</t-button>
      </t-space>
    </div>

    <div class="ds-card">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">状态</div>
          <t-tag :theme="record.status === 'success' ? 'success' : 'danger'">{{ record.status === 'success' ? '成功' : '失败' }}</t-tag>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">文件路径</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 13px; word-break: break-all;">{{ record.file_path }}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">文件大小</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 14px;">
            <span v-if="record.uncompressed_size">
              {{ fmtBytes(record.uncompressed_size) }} <span style="color: var(--ds-text-secondary);">({{ fmtBytes(record.file_size) }})</span>
            </span>
            <span v-else>{{ fmtBytes(record.file_size) }}</span>
          </div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">校验值</div>
          <div style="font-family: 'Fira Code', monospace; font-size: 11px; word-break: break-all;">{{ record.checksum }}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">开始时间</div>
          <div style="font-size: 14px;">{{ fmtDatetime(record.started_at) }}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">完成时间</div>
          <div style="font-size: 14px;">{{ fmtDatetime(record.finished_at) }}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: var(--ds-text-secondary); margin-bottom: 4px;">运行时间</div>
          <div style="font-size: 14px;">{{ formatDuration(record.started_at, record.finished_at) }}</div>
        </div>
      </div>
      <t-alert v-if="record.error_message" theme="error" :message="record.error_message" style="margin-top:16px" />
    </div>

    <!-- 恢复对话框 -->
    <t-dialog
      v-model:visible="restoreDialogVisible"
      header="恢复备份"
      :confirm-btn="{ content: '确认恢复', theme: 'primary' }"
      :cancel-btn="{ content: '取消', variant: 'outline' }"
      @confirm="handleRestore"
      width="600px"
    >
      <div class="restore-form">
        <p style="color: var(--ds-text-secondary); margin-bottom: 16px;">
          选择要恢复到的目标数据库。如不选择，将恢复到原数据库。
        </p>

        <t-form :data="restoreForm">
          <t-form-item label="选择已有数据源">
            <t-select
              v-model="restoreForm.target_datasource_id"
              :options="datasources.map((d: any) => ({ label: `${d.name} (${d.type})`, value: d.id }))"
              placeholder="选择已有数据源（可选）"
              clearable
            />
          </t-form-item>

          <div style="text-align: center; margin: 16px 0; color: var(--ds-text-secondary);">— 或手动填写 —</div>

          <t-form-item label="数据库类型">
            <t-radio-group v-model="restoreForm.target_db_type">
              <t-radio value="mysql">MySQL</t-radio>
              <t-radio value="postgresql">PostgreSQL</t-radio>
            </t-radio-group>
          </t-form-item>

          <t-form-item label="Host">
            <t-input v-model="restoreForm.target_host" placeholder="数据库主机地址" />
          </t-form-item>

          <t-form-item label="Port">
            <t-input-number v-model="restoreForm.target_port" :min="1" :max="65535" placeholder="端口" />
          </t-form-item>

          <t-form-item label="用户名">
            <t-input v-model="restoreForm.target_username" placeholder="数据库用户名" />
          </t-form-item>

          <t-form-item label="密码">
            <t-input v-model="restoreForm.target_password" type="password" placeholder="数据库密码" />
          </t-form-item>

          <t-form-item label="数据库名">
            <t-input v-model="restoreForm.target_database" placeholder="目标数据库名" />
          </t-form-item>
        </t-form>
      </div>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";
import { fmtDatetime, fmtBytes } from "../utils/format";

const route = useRoute();
const record = ref<any>(null);
const datasources = ref<any[]>([]);
const restoreDialogVisible = ref(false);
const restoreForm = ref({
  target_datasource_id: null as number | null,
  target_db_type: "mysql",
  target_host: "",
  target_port: 3306,
  target_username: "",
  target_password: "",
  target_database: "",
});

function toUtcTimestamp(val: string): number {
  const raw = val.includes("T") && !val.endsWith("Z") ? val + "Z" : val;
  return new Date(raw).getTime();
}

function formatDuration(start: string, finish: string | null) {
  if (!start || !finish) return "-";
  const diff = toUtcTimestamp(finish) - toUtcTimestamp(start);
  if (diff < 0) return "-";
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}秒`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}分${s % 60}秒`;
  const h = Math.floor(m / 60);
  return `${h}小时${m % 60}分${s % 60}秒`;
}

onMounted(async () => {
  const [rec, ds] = await Promise.all([
    api.getBackupRecord(Number(route.params.rid)),
    api.listDatasources(),
  ]);
  record.value = rec;
  datasources.value = ds;
});

function showRestoreDialog() {
  restoreDialogVisible.value = true;
  // Reset form
  restoreForm.value = {
    target_datasource_id: null,
    target_db_type: "mysql",
    target_host: "",
    target_port: 3306,
    target_username: "",
    target_password: "",
    target_database: "",
  };
}

async function handleRestore() {
  try {
    const target: any = {};
    
    if (restoreForm.value.target_datasource_id) {
      target.target_datasource_id = restoreForm.value.target_datasource_id;
    } else if (restoreForm.value.target_host) {
      target.target_host = restoreForm.value.target_host;
      target.target_port = restoreForm.value.target_port;
      target.target_username = restoreForm.value.target_username;
      target.target_password = restoreForm.value.target_password;
      target.target_database = restoreForm.value.target_database;
      target.target_db_type = restoreForm.value.target_db_type;
    }
    
    await api.restoreBackup(record.value!.id, target);
    MessagePlugin.success("恢复任务已触发");
    restoreDialogVisible.value = false;
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}
</script>

<style scoped>
.restore-form {
  padding: 8px 0;
}
</style>
