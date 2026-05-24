import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { api } from "../api/client";

export interface BackupTask {
  id: number;
  name: string;
  datasource_id: number;
  backup_type: "full" | "incremental";
  schedule_config: { cron: string } | null;
  storage_path: string;
  retention_days: number;
  compression: boolean;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface BackupRecord {
  id: number;
  task_id: number;
  status: "running" | "success" | "fail";
  started_at: string;
  finished_at: string | null;
  file_path: string | null;
  file_size: number | null;
  checksum: string | null;
  error_message: string | null;
}

export const useBackupStore = defineStore("backup", () => {
  const tasks = ref<BackupTask[]>([]);
  const records = ref<BackupRecord[]>([]);
  const loading = ref(false);
  const currentTask = ref<BackupTask | null>(null);

  const scheduledTasks = computed(() => tasks.value.filter((t) => t.schedule_config));
  const enabledTasks = computed(() => tasks.value.filter((t) => t.is_enabled));
  const recentRecords = computed(() => records.value.slice(0, 10));

  async function fetchTasks() {
    loading.value = true;
    try {
      tasks.value = await api.listBackupTasks();
    } finally {
      loading.value = false;
    }
  }

  async function fetchRecords(taskId?: number) {
    loading.value = true;
    try {
      records.value = await api.listBackupRecords(taskId);
    } finally {
      loading.value = false;
    }
  }

  async function fetchTask(id: number) {
    loading.value = true;
    try {
      currentTask.value = await api.getBackupTask(id);
    } finally {
      loading.value = false;
    }
  }

  async function createTask(data: Partial<BackupTask>) {
    const result = await api.createBackupTask(data);
    tasks.value.push(result);
    return result;
  }

  async function updateTask(id: number, data: Partial<BackupTask>) {
    const result = await api.updateBackupTask(id, data);
    const idx = tasks.value.findIndex((t) => t.id === id);
    if (idx !== -1) tasks.value[idx] = result;
    return result;
  }

  async function deleteTask(id: number) {
    await api.deleteBackupTask(id);
    tasks.value = tasks.value.filter((t) => t.id !== id);
  }

  async function runTask(id: number) {
    return api.runBackupTask(id);
  }

  async function restoreRecord(id: number, target?: any) {
    return api.restoreBackup(id, target);
  }

  async function toggleTask(id: number, isEnabled: boolean) {
    const result = await api.updateBackupTask(id, { is_enabled: isEnabled });
    const idx = tasks.value.findIndex((t) => t.id === id);
    if (idx !== -1) tasks.value[idx] = result;
    return result;
  }

  return {
    tasks,
    records,
    loading,
    currentTask,
    scheduledTasks,
    enabledTasks,
    recentRecords,
    fetchTasks,
    fetchRecords,
    fetchTask,
    createTask,
    updateTask,
    deleteTask,
    runTask,
    restoreRecord,
    toggleTask,
  };
});
