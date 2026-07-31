import axios from "axios";
import type {
  Asset,
  AssetListResponse,
  AssetStats,
  Collection,
  AssetHistory,
  AssetRelationship,
} from "../types/asset";

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

export const assetApi = {
  list: (
    params: {
      project_id?: string;
      query?: string;
      asset_type?: string;
      category?: string;
      extension?: string;
      tags?: string;
      owner?: string;
      favorite_only?: boolean;
      sort_by?: string;
      sort_order?: string;
      offset?: number;
      limit?: number;
    } = {}
  ) => api.get<AssetListResponse>("/assets", { params }),

  search: (q: string, params: { project_id?: string; asset_type?: string } = {}) =>
    api.get<AssetListResponse>("/assets/search", { params: { q, ...params } }),

  get: (id: string) => api.get<Asset>(`/assets/${id}`),

  update: (id: string, data: { name?: string; display_name?: string; description?: string; category?: string }) =>
    api.put<Asset>(`/assets/${id}`, data),

  delete: (id: string) => api.delete(`/assets/${id}`),

  toggleFavorite: (id: string) => api.post<{ is_favorite: boolean }>(`/assets/${id}/favorite`),

  togglePin: (id: string) => api.post<{ is_pinned: boolean }>(`/assets/${id}/pin`),

  archive: (id: string) => api.post<{ success: boolean }>(`/assets/${id}/archive`),

  restore: (id: string) => api.post<{ success: boolean }>(`/assets/${id}/restore`),

  addTag: (id: string, tag: string) => api.post(`/assets/${id}/tag`, { tag }),

  removeTag: (id: string, tag: string) => api.delete(`/assets/${id}/tag/${tag}`),

  addRelationship: (id: string, targetId: string, type: string) =>
    api.post(`/assets/${id}/relationship`, { target_asset_id: targetId, relationship_type: type }),

  getRelated: (id: string) => api.get<{ related: AssetRelationship[] }>(`/assets/${id}/related`),

  getHistory: (id: string) => api.get<AssetHistory[]>(`/assets/${id}/history`),

  getCollections: (id: string) => api.get<Collection[]>(`/assets/${id}/collections`),

  getStats: (projectId: string) => api.get<AssetStats>(`/assets/stats/${projectId}`),

  importFile: (
    file: File,
    options: { project_id?: string; name?: string; description?: string; category?: string; tags?: string } = {}
  ) => {
    const formData = new FormData();
    formData.append("file", file);
    const params = new URLSearchParams();
    if (options.project_id) params.append("project_id", options.project_id);
    if (options.name) params.append("name", options.name);
    if (options.description) params.append("description", options.description);
    if (options.category) params.append("category", options.category);
    if (options.tags) params.append("tags", options.tags);

    return api.post(`/assets/import?${params.toString()}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // Collections
  createCollection: (data: { name: string; description?: string; project_id?: string }) =>
    api.post<Collection>("/assets/collections", data),

  listCollections: (projectId?: string) =>
    api.get<{ collections: Collection[]; total: number }>("/assets/collections/list", {
      params: { project_id: projectId },
    }),

  addToCollection: (collectionId: string, assetId: string) =>
    api.post(`/assets/collections/${collectionId}/add?asset_id=${assetId}`),

  getCollectionAssets: (collectionId: string) =>
    api.get<Asset[]>(`/assets/collections/${collectionId}/assets`),
};
