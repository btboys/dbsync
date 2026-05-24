<template>
  <t-card v-if="record" title="备份记录详情">
    <t-descriptions>
      <t-descriptions-item label="状态">
        <t-tag :theme="record.status === 'success' ? 'success' : 'danger'">{{ record.status }}</t-tag>
      </t-descriptions-item>
      <t-descriptions-item label="文件路径">{{ record.file_path }}</t-descriptions-item>
      <t-descriptions-item label="文件大小">{{ record.file_size }} bytes</t-descriptions-item>
      <t-descriptions-item label="校验值">{{ record.checksum }}</t-descriptions-item>
      <t-descriptions-item label="开始时间">{{ record.started_at }}</t-descriptions-item>
      <t-descriptions-item label="完成时间">{{ record.finished_at }}</t-descriptions-item>
      <t-descriptions-item v-if="record.error_message" label="错误信息" :span="3">
        <t-alert theme="error" :message="record.error_message" />
      </t-descriptions-item>
    </t-descriptions>
    <t-space style="margin-top: 16px">
      <t-button v-if="record.status === 'success'" @click="handleRestore">恢复到此备份</t-button>
      <t-button variant="outline" @click="$router.back()">返回</t-button>
    </t-space>
  </t-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";

const route = useRoute();
const record = ref<any>(null);

onMounted(async () => {
  record.value = await api.getBackupRecord(Number(route.params.rid));
});

async function handleRestore() {
  try {
    await api.restoreBackup(record.value!.id);
    MessagePlugin.success("恢复任务已触发");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}
</script>
