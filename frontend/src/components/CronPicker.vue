<template>
  <div class="cron-picker">
    <t-radio-group v-model="freq" @change="onChange">
      <t-radio value="">手动触发</t-radio>
      <t-radio value="hourly">每小时</t-radio>
      <t-radio value="daily">每天</t-radio>
      <t-radio value="weekly">每周</t-radio>
      <t-radio value="monthly">每月</t-radio>
    </t-radio-group>

    <div v-if="freq === 'daily'" class="cron-detail">
      <span class="cron-label">每天</span>
      <t-select v-model="hour" style="width:100px" @change="onChange">
        <t-option v-for="h in 24" :key="h - 1" :value="h - 1" :label="`${String(h - 1).padStart(2, '0')}:00`" />
      </t-select>
    </div>

    <div v-if="freq === 'weekly'" class="cron-detail">
      <t-select v-model="weekday" style="width:140px" @change="onChange">
        <t-option value="1" label="每周一" />
        <t-option value="2" label="每周二" />
        <t-option value="3" label="每周三" />
        <t-option value="4" label="每周四" />
        <t-option value="5" label="每周五" />
        <t-option value="6" label="每周六" />
        <t-option value="0" label="每周日" />
      </t-select>
      <span class="cron-label">执行时间</span>
      <t-select v-model="hour" style="width:100px" @change="onChange">
        <t-option v-for="h in 24" :key="h - 1" :value="h - 1" :label="`${String(h - 1).padStart(2, '0')}:00`" />
      </t-select>
    </div>

    <div v-if="freq === 'monthly'" class="cron-detail cron-monthly">
      <div class="cron-field">
        <span class="cron-label">每月第</span>
        <t-input-number v-model="dayOfMonth" :min="1" :max="28" />
        <span class="cron-label">天</span>
      </div>
      <div class="cron-field">
        <span class="cron-label">执行时间</span>
        <t-select v-model="hour" style="width:100px" @change="onChange">
          <t-option v-for="h in 24" :key="h - 1" :value="h - 1" :label="`${String(h - 1).padStart(2, '0')}:00`" />
        </t-select>
      </div>
    </div>

    <div v-if="cronValue" class="cron-preview">
      <code>{{ cronValue }}</code>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

const props = defineProps<{
  modelValue: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", val: string): void;
}>();

const freq = ref("");
const hour = ref(2);
const weekday = ref("1");
const dayOfMonth = ref(1);
const cronValue = ref("");

function buildCron() {
  let cron = "";
  switch (freq.value) {
    case "hourly":
      cron = "0 * * * *";
      break;
    case "daily":
      cron = `0 ${hour.value} * * *`;
      break;
    case "weekly":
      cron = `0 ${hour.value} * * ${weekday.value}`;
      break;
    case "monthly":
      cron = `0 ${hour.value} ${dayOfMonth.value} * *`;
      break;
    default:
      cron = "";
  }
  cronValue.value = cron;
  emit("update:modelValue", cron);
}

function onChange() {
  buildCron();
}

// Parse initial value
watch(
  () => props.modelValue,
  (val) => {
    if (!val) {
      freq.value = "";
      return;
    }
    const parts = val.split(" ");
    if (parts.length !== 5) return;
    const [min, hr, day, mon, week] = parts;
    if (min === "0" && hr === "*" && day === "*" && mon === "*" && week === "*") {
      freq.value = "hourly";
    } else if (day === "*" && mon === "*" && week === "*") {
      freq.value = "daily";
      hour.value = parseInt(hr);
    } else if (day === "*" && mon === "*" && week !== "*") {
      freq.value = "weekly";
      hour.value = parseInt(hr);
      weekday.value = week;
    } else if (mon === "*" && week === "*") {
      freq.value = "monthly";
      hour.value = parseInt(hr);
      dayOfMonth.value = parseInt(day);
    }
    cronValue.value = val;
  },
  { immediate: true }
);
</script>

<style scoped>
.cron-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cron-detail {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cron-label {
  font-size: 13px;
  color: var(--ds-text-secondary);
  white-space: nowrap;
}

.cron-monthly {
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}

.cron-field {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cron-field .t-input-number {
  width: 100px;
}

.cron-preview {
  padding: 6px 10px;
  background: var(--ds-bg);
  border-radius: 4px;
}

.cron-preview code {
  font-family: 'Fira Code', monospace;
  font-size: 13px;
  color: var(--ds-primary);
}
</style>
