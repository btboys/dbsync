const BASE = "/api/v1";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Datasources
  listDatasources: () => request<any[]>("/datasources"),
  getDatasource: (id: number) => request<any>(`/datasources/${id}`),
  createDatasource: (data: any) =>
    request<any>("/datasources", { method: "POST", body: JSON.stringify(data) }),
  updateDatasource: (id: number, data: any) =>
    request<any>(`/datasources/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteDatasource: (id: number) =>
    request<void>(`/datasources/${id}`, { method: "DELETE" }),
  testDatasource: (id: number) =>
    request<{ status: string }>(`/datasources/${id}/test`, { method: "POST" }),

  // Backup
  listBackupTasks: () => request<any[]>("/backup-tasks"),
  getBackupTask: (id: number) => request<any>(`/backup-tasks/${id}`),
  createBackupTask: (data: any) =>
    request<any>("/backup-tasks", { method: "POST", body: JSON.stringify(data) }),
  updateBackupTask: (id: number, data: any) =>
    request<any>(`/backup-tasks/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteBackupTask: (id: number) =>
    request<void>(`/backup-tasks/${id}`, { method: "DELETE" }),
  runBackupTask: (id: number) =>
    request<any>(`/backup-tasks/${id}/run`, { method: "POST" }),
  listBackupRecords: (taskId?: number, status?: string) =>
    request<any[]>(`/backup-records?${taskId ? `task_id=${taskId}&` : ""}${status ? `status=${status}` : ""}`),
  getBackupRecord: (id: number) => request<any>(`/backup-records/${id}`),
  restoreBackup: (id: number) =>
    request<any>(`/backup-records/${id}/restore`, { method: "POST" }),
  cancelBackupRecord: (id: number) =>
    request<any>(`/backup-records/${id}/cancel`, { method: "POST" }),

  // Migration
  listMigrationTasks: () => request<any[]>("/migration-tasks"),
  getMigrationTask: (id: number) => request<any>(`/migration-tasks/${id}`),
  createMigrationTask: (data: any) =>
    request<any>("/migration-tasks", { method: "POST", body: JSON.stringify(data) }),
  updateMigrationTask: (id: number, data: any) =>
    request<any>(`/migration-tasks/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteMigrationTask: (id: number) =>
    request<void>(`/migration-tasks/${id}`, { method: "DELETE" }),
  runMigrationTask: (id: number) =>
    request<any>(`/migration-tasks/${id}/run`, { method: "POST" }),
  listMigrationRecords: (taskId?: number, status?: string) =>
    request<any[]>(`/migration-records?${taskId ? `task_id=${taskId}&` : ""}${status ? `status=${status}` : ""}`),

  // Logs
  listTaskLogs: (params?: { task_type?: string; task_record_id?: number; level?: string }) => {
    const search = params ? new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined) as [string, string][]).toString() : "";
    return request<any[]>(`/task-logs${search ? `?${search}` : ""}`);
  },
};
