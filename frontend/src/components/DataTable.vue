<template>
  <t-table
    :data="data"
    :columns="columns"
    :row-key="rowKey"
    :loading="loading"
    :pagination="pagination"
    :selected-row-keys="selectedRowKeys"
    @page-change="handlePageChange"
    @select-change="handleSelectChange"
  >
    <!-- 插槽透传 -->
    <template v-for="slotName in Object.keys($slots)" :key="slotName" #[slotName]="slotProps">
      <slot :name="slotName" v-bind="slotProps || {}" />
    </template>
  </t-table>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Pagination {
  current: number;
  pageSize: number;
  total: number;
  showJumper?: boolean;
  showPageSize?: boolean;
}

const props = defineProps<{
  data: any[];
  columns: any[];
  rowKey?: string;
  loading?: boolean;
  pagination?: Partial<Pagination>;
  selectedRowKeys?: (string | number)[];
}>();

const emit = defineEmits<{
  (e: "page-change", pageInfo: { current: number; previous: number; pageSize: number }): void;
  (e: "select-change", value: (string | number)[], { selectedRowData }: { selectedRowData: any[] }): void;
}>();

const defaultPagination = computed(() => ({
  current: 1,
  pageSize: 10,
  total: props.data.length,
  showJumper: true,
  showPageSize: true,
  ...props.pagination,
}));

function handlePageChange(pageInfo: { current: number; previous: number; pageSize: number }) {
  emit("page-change", pageInfo);
}

function handleSelectChange(value: (string | number)[], extra: { selectedRowData: any[] }) {
  emit("select-change", value, extra);
}
</script>
