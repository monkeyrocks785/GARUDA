import axios from "axios";
import type {
  Dataset,
  DatasetListResponse,
  DatasetStats,
  DatasetVersion,
  ImportResult,
  ImportMultipleResult,
} from "../types/dataset";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const datasetApi = {
  list: (
    projectId: string,
    params: {
      query?: string;
      dataset_type?: string;
      extension?: string;
      tags?: string;
      favorite_only?: boolean;
      sort_by?: string;
      sort_order?: string;
      offset?: number;
      limit?: number;
    } = {}
  ) =>
    api.get<DatasetListResponse>("/datasets", {
      params: { project_id: projectId, ...params },
    }),

  search: (
    projectId: string,
    q: string,
    params: {
      dataset_type?: string;
      extension?: string;
      tags?: string;
      favorite_only?: boolean;
    } = {}
  ) =>
    api.get<DatasetListResponse>("/datasets/search", {
      params: { project_id: projectId, q, ...params },
    }),

  get: (datasetId: string) => api.get<Dataset>(`/datasets/${datasetId}`),

  update: (datasetId: string, data: { name?: string; description?: string; notes?: string }) =>
    api.put<Dataset>(`/datasets/${datasetId}`, data),

  delete: (datasetId: string) => api.delete(`/datasets/${datasetId}`),

  toggleFavorite: (datasetId: string) =>
    api.post<{ is_favorite: boolean }>(`/datasets/${datasetId}/favorite`),

  addTag: (datasetId: string, tag: string) =>
    api.post(`/datasets/${datasetId}/tag`, { tag }),

  removeTag: (datasetId: string, tag: string) =>
    api.delete(`/datasets/${datasetId}/tag/${tag}`),

  getVersions: (datasetId: string) =>
    api.get<DatasetVersion[]>(`/datasets/${datasetId}/versions`),

  getMetadata: (datasetId: string) =>
    api.get<Record<string, { value: string; category: string }>>(`/datasets/${datasetId}/metadata`),

  getStats: (projectId: string) =>
    api.get<DatasetStats>(`/datasets/stats/${projectId}`),

  importFile: (
    projectId: string,
    file: File,
    options: { name?: string; description?: string; tags?: string } = {}
  ) => {
    const formData = new FormData();
    formData.append("file", file);
    if (options.name) formData.append("name", options.name);
    if (options.description) formData.append("description", options.description);
    if (options.tags) formData.append("tags", options.tags);

    return api.post<ImportResult>(
      `/datasets/import?project_id=${projectId}`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
  },

  importFolder: (
    projectId: string,
    folderPath: string,
    recursive: boolean = true
  ) =>
    api.post<ImportMultipleResult>(
      `/datasets/import-folder?project_id=${projectId}&folder_path=${encodeURIComponent(folderPath)}&recursive=${recursive}`
    ),
};
