<template>
  <t-row justify="space-between" align="middle" class="page-header">
    <div class="page-title">
      <t-icon v-if="icon" :name="icon" class="title-icon" />
      <h2>{{ title }}</h2>
    </div>
    <t-space>
      <slot name="actions"></slot>
    </t-space>
  </t-row>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  icon?: string;
}>();
</script>

<style scoped>
.page-header {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e7e7e7;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.title-icon {
  font-size: 24px;
  color: #0052d9;
}
</style>
