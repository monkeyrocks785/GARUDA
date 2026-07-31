import axios from "axios";
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectListResponse,
  ProjectStats,
  RecoveryResponse,
  AOI,
  AOICreate,
  AOIUpdate,
  Layer,
  LayerCreate,
  LayerUpdate,
  ImportResponse,
  ExportRequest,
  ExportResponse,
} from "../types";

const api = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================================
// Health API
// ============================================================

export interface HealthResponse {
  status: string;
  version: string;
  uptime: string;
  environment: string;
  timestamp: string;
}

export interface DetailedHealthResponse {
  status: string;
  database: string;
  timestamp: string;
}

export const healthApi = {
  getHealth: () => api.get<HealthResponse>("/health"),
  getDetailedHealth: () => api.get<DetailedHealthResponse>("/health/detailed"),
};

// ============================================================
// Project API
// ============================================================

export const projectApi = {
  create: (data: ProjectCreate) => api.post<Project>("/projects", data),

  list: (params?: {
    include_archived?: boolean;
    search?: string;
    offset?: number;
    limit?: number;
  }) => api.get<ProjectListResponse>("/projects", { params }),

  getById: (id: string) => api.get<Project>(`/projects/${id}`),

  update: (id: string, data: ProjectUpdate) =>
    api.put<Project>(`/projects/${id}`, data),

  delete: (id: string, deleteFiles = true) =>
    api.delete(`/projects/${id}`, { params: { delete_files: deleteFiles } }),

  archive: (id: string) => api.post<Project>(`/projects/${id}/archive`),

  unarchive: (id: string) => api.post<Project>(`/projects/${id}/unarchive`),

  toggleFavorite: (id: string) => api.post<Project>(`/projects/${id}/favorite`),

  duplicate: (id: string, newName?: string) =>
    api.post<Project>(`/projects/${id}/duplicate`, null, {
      params: newName ? { new_name: newName } : undefined,
    }),

  open: (id: string) => api.post<Project>(`/projects/${id}/open`),

  updateWorkState: (id: string, data: Partial<Project>) =>
    api.put<Project>(`/projects/${id}/work-state`, data),

  getRecent: (limit = 10) =>
    api.get<Project[]>("/projects/recent", { params: { limit } }),

  getFavorites: (limit = 50) =>
    api.get<Project[]>("/projects/favorites", { params: { limit } }),

  getStats: () => api.get<ProjectStats>("/projects/stats"),

  checkRecovery: () => api.get<RecoveryResponse>("/projects/recovery"),
};

// ============================================================
// AOI API
// ============================================================

export const aoiApi = {
  create: (projectId: string, data: AOICreate) =>
    api.post<AOI>(`/projects/${projectId}/aoi`, data),

  list: (projectId: string) =>
    api.get<AOI[]>(`/projects/${projectId}/aoi`),

  getById: (projectId: string, aoiId: string) =>
    api.get<AOI>(`/projects/${projectId}/aoi/${aoiId}`),

  update: (projectId: string, aoiId: string, data: AOIUpdate) =>
    api.put<AOI>(`/projects/${projectId}/aoi/${aoiId}`, data),

  delete: (projectId: string, aoiId: string) =>
    api.delete(`/projects/${projectId}/aoi/${aoiId}`),
};

// ============================================================
// Layer API
// ============================================================

export const layerApi = {
  create: (projectId: string, data: LayerCreate) =>
    api.post<Layer>(`/projects/${projectId}/layers`, data),

  list: (projectId: string) =>
    api.get<Layer[]>(`/projects/${projectId}/layers`),

  getById: (projectId: string, layerId: string) =>
    api.get<Layer>(`/projects/${projectId}/layers/${layerId}`),

  update: (projectId: string, layerId: string, data: LayerUpdate) =>
    api.put<Layer>(`/projects/${projectId}/layers/${layerId}`, data),

  toggleVisibility: (projectId: string, layerId: string) =>
    api.post<Layer>(`/projects/${projectId}/layers/${layerId}/toggle-visibility`),

  delete: (projectId: string, layerId: string) =>
    api.delete(`/projects/${projectId}/layers/${layerId}`),

  reorder: (projectId: string, layerIds: string[]) =>
    api.post<Layer[]>(`/projects/${projectId}/layers/reorder`, { layer_ids: layerIds }),
};

// ============================================================
// Import API
// ============================================================

export const importApi = {
  geojson: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<ImportResponse>(`/projects/${projectId}/import/geojson`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  kml: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<ImportResponse>(`/projects/${projectId}/import/kml`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  shapefile: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<ImportResponse>(`/projects/${projectId}/import/shapefile`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// ============================================================
// Export API
// ============================================================

export const exportApi = {
  geojson: (projectId: string, data: ExportRequest) =>
    api.post<ExportResponse>(`/projects/${projectId}/export/geojson`, data),

  kml: (projectId: string, data: ExportRequest) =>
    api.post<ExportResponse>(`/projects/${projectId}/export/kml`, data),
};

export default api;
