<template>
  <t-layout>
    <t-aside>
      <t-menu :default-value="activeRoute" theme="dark">
        <div class="logo">DBSync</div>
        <t-menu-item value="dashboard" to="/">
          <template #icon><t-icon name="dashboard" /></template>
          仪表盘
        </t-menu-item>
        <t-menu-item value="datasources" to="/datasources">
          <template #icon><t-icon name="database" /></template>
          数据源
        </t-menu-item>
        <t-menu-item value="backup" to="/backup">
          <template #icon><t-icon name="backup" /></template>
          备份
        </t-menu-item>
        <t-menu-item value="restore" to="/restore">
          <template #icon><t-icon name="rollback" /></template>
          恢复
        </t-menu-item>
        <t-menu-item value="migration" to="/migration">
          <template #icon><t-icon name="swap" /></template>
          迁移
        </t-menu-item>
        <t-menu-item value="schedules" to="/schedules">
          <template #icon><t-icon name="time" /></template>
          定时策略
        </t-menu-item>
        <t-menu-item value="logs" to="/logs">
          <template #icon><t-icon name="file-text" /></template>
          日志
        </t-menu-item>
      </t-menu>
    </t-aside>
    <t-layout>
      <t-content class="main-content">
        <router-view />
      </t-content>
    </t-layout>
  </t-layout>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const activeRoute = computed(() => route.path.split("/")[1] || "dashboard");
</script>

<style>
body { margin: 0; }
.logo { padding: 20px; font-size: 20px; font-weight: bold; color: #fff; text-align: center; }
.main-content { padding: 24px; min-height: 100vh; background: #f5f5f5; }
</style>
