<template>
  <t-card v-if="ds" :title="ds.name">
    <t-descriptions>
      <t-descriptions-item label="类型">{{ ds.type }}</t-descriptions-item>
      <t-descriptions-item label="主机">{{ ds.host }}</t-descriptions-item>
      <t-descriptions-item label="端口">{{ ds.port }}</t-descriptions-item>
      <t-descriptions-item label="数据库">{{ ds.database }}</t-descriptions-item>
      <t-descriptions-item label="用户名">{{ ds.username }}</t-descriptions-item>
      <t-descriptions-item label="状态">
        <t-switch :value="ds.is_active" disabled size="small" />
      </t-descriptions-item>
    </t-descriptions>
    <t-space style="margin-top: 16px">
      <t-button @click="handleTest">测试连接</t-button>
      <t-button variant="outline" @click="$router.push('/datasources')">返回</t-button>
    </t-space>
  </t-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { MessagePlugin } from "tdesign-vue-next";
import { api } from "../api/client";

const route = useRoute();
const ds = ref<any>(null);

onMounted(async () => {
  ds.value = await api.getDatasource(Number(route.params.id));
});

async function handleTest() {
  try {
    const res = await api.testDatasource(ds.value.id);
    MessagePlugin.success("连接成功");
  } catch (e: any) {
    MessagePlugin.error(e.message);
  }
}
</script>
