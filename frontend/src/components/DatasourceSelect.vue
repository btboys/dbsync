<template>
  <t-form-item :label="label" :name="name" :rules="rules">
    <t-select
      v-model="modelValue"
      :options="options"
      :placeholder="placeholder"
      :clearable="clearable"
      :disabled="disabled"
      @change="handleChange"
    />
  </t-form-item>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: any;
  label: string;
  name?: string;
  options: { label: string; value: any }[];
  placeholder?: string;
  clearable?: boolean;
  disabled?: boolean;
  rules?: any[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: any): void;
  (e: "change", value: any): void;
}>();

function handleChange(value: any) {
  emit("update:modelValue", value);
  emit("change", value);
}
</script>
