import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { api } from "../api/client";

export interface Datasource {
  id: number;
  name: string;
  type: "mysql" | "postgresql";
  host: string;
  port: number;
  username: string;
  database: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const useDatasourceStore = defineStore("datasource", () => {
  const datasources = ref<Datasource[]>([]);
  const loading = ref(false);
  const currentDatasource = ref<Datasource | null>(null);

  const mysqlCount = computed(() => datasources.value.filter((d) => d.type === "mysql").length);
  const pgCount = computed(() => datasources.value.filter((d) => d.type === "postgresql").length);

  async function fetchDatasources() {
    loading.value = true;
    try {
      datasources.value = await api.listDatasources();
    } finally {
      loading.value = false;
    }
  }

  async function fetchDatasource(id: number) {
    loading.value = true;
    try {
      currentDatasource.value = await api.getDatasource(id);
    } finally {
      loading.value = false;
    }
  }

  async function createDatasource(data: Partial<Datasource>) {
    const result = await api.createDatasource(data);
    datasources.value.push(result);
    return result;
  }

  async function updateDatasource(id: number, data: Partial<Datasource>) {
    const result = await api.updateDatasource(id, data);
    const idx = datasources.value.findIndex((d) => d.id === id);
    if (idx !== -1) datasources.value[idx] = result;
    return result;
  }

  async function deleteDatasource(id: number) {
    await api.deleteDatasource(id);
    datasources.value = datasources.value.filter((d) => d.id !== id);
  }

  async function testConnection(id: number) {
    return api.testDatasource(id);
  }

  return {
    datasources,
    loading,
    currentDatasource,
    mysqlCount,
    pgCount,
    fetchDatasources,
    fetchDatasource,
    createDatasource,
    updateDatasource,
    deleteDatasource,
    testConnection,
  };
});
