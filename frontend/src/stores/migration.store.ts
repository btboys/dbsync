import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { api } from "../api/client";

export interface MigrationTask {
  id: number;
  name: string;
  source_datasource_id: number;
  target_datasource_id: number;
  table_include: string[] | null;
  table_exclude: string[] | null;
  transfer_type: "schema_only" | "data_only" | "schema_and_data";
  created_at: string;
  updated_at: string;
}

export interface MigrationRecord {
  id: number;
  task_id: number;
  status: "running" | "success" | "fail";
  started_at: string;
  finished_at: string | null;
  rows_transferred: number | null;
  error_message: string | null;
}

export const useMigrationStore = defineStore("migration", () => {
  const tasks = ref<MigrationTask[]>([]);
  const records = ref<MigrationRecord[]>([]);
  const loading = ref(false);
  const currentTask = ref<MigrationTask | null>(null);

  const schemaOnlyTasks = computed(() => tasks.value.filter((t) => t.transfer_type === "schema_only"));
  const dataOnlyTasks = computed(() => tasks.value.filter((t) => t.transfer_type === "data_only"));
  const fullTasks = computed(() => tasks.value.filter((t) => t.transfer_type === "schema_and_data"));

  async function fetchTasks() {
    loading.value = true;
    try {
      tasks.value = await api.listMigrationTasks();
    } finally {
      loading.value = false;
    }
  }

  async function fetchRecords(taskId?: number) {
    loading.value = true;
    try {
      records.value = await api.listMigrationRecords(taskId);
    } finally {
      loading.value = false;
    }
  }

  async function fetchTask(id: number) {
    loading.value = true;
    try {
      currentTask.value = await api.getMigrationTask(id);
    } finally {
      loading.value = false;
    }
  }

  async function createTask(data: Partial<MigrationTask>) {
    const result = await api.createMigrationTask(data);
    tasks.value.push(result);
    return result;
  }

  async function updateTask(id: number, data: Partial<MigrationTask>) {
    const result = await api.updateMigrationTask(id, data);
    const idx = tasks.value.findIndex((t) => t.id === id);
    if (idx !== -1) tasks.value[idx] = result;
    return result;
  }

  async function deleteTask(id: number) {
    await api.deleteMigrationTask(id);
    tasks.value = tasks.value.filter((t) => t.id !== id);
  }

  async function runTask(id: number) {
    return api.runMigrationTask(id);
  }

  return {
    tasks,
    records,
    loading,
    currentTask,
    schemaOnlyTasks,
    dataOnlyTasks,
    fullTasks,
    fetchTasks,
    fetchRecords,
    fetchTask,
    createTask,
    updateTask,
    deleteTask,
    runTask,
  };
});
