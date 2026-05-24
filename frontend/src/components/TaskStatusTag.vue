<template>
  <t-tag
    :theme="theme"
    :variant="variant"
    :size="size"
  >
    {{ displayText }}
  </t-tag>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  status: string;
  type?: "backup" | "migration" | "general";
  size?: "small" | "medium" | "large";
  variant?: "dark" | "light" | "outline" | "light-outline";
}>();

const theme = computed(() => {
  const status = props.status?.toLowerCase() || "";
  switch (status) {
    case "success":
    case "completed":
      return "success";
    case "running":
    case "pending":
    case "processing":
      return "warning";
    case "fail":
    case "failed":
    case "error":
      return "danger";
    case "cancelled":
      return "default";
    case "info":
      return "primary";
    default:
      return "default";
  }
});

const displayText = computed(() => {
  const status = props.status?.toLowerCase() || "";
  const textMap: Record<string, string> = {
    success: "成功",
    fail: "失败",
    running: "执行中",
    pending: "待处理",
    completed: "已完成",
    cancelled: "已取消",
    error: "错误",
    info: "信息",
  };
  return textMap[status] || status;
});
</script>
