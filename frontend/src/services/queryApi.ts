import api from "./api";
import type {
  QueryConfig,
  QueryRequest,
  QueryResult,
  SaveQueryRequest,
  SavedQuery,
  UpdateQueryRequest,
  QueryHistoryEntry,
  ExportRequest,
  ExportResult,
  PaginatedResponse,
} from "../types/query";

export const queryApi = {
  // ── Config ────────────────────────────────────────────────────────────
  getConfig: () => api.get<QueryConfig>("/queries/config"),

  // ── Query Execution ──────────────────────────────────────────────────
  executeQuery: (data: QueryRequest, useCache = false) =>
    api.post<QueryResult>(`/queries/execute?use_cache=${useCache}`, data),

  executeRawQuery: (
    filters: Record<string, unknown>,
    projectId: string,
    page = 0,
    pageSize = 50,
    enrich = false,
  ) =>
    api.post<QueryResult>(
      `/queries/execute/raw?project_id=${projectId}&page=${page}&page_size=${pageSize}&enrich=${enrich}`,
      filters,
    ),

  // ── Saved Queries ────────────────────────────────────────────────────
  saveQuery: (data: SaveQueryRequest) =>
    api.post<SavedQuery>("/queries/saved", data),

  listSavedQueries: (projectId: string, params?: {
    favorite_only?: boolean;
    pinned_only?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
  }) =>
    api.get<PaginatedResponse<SavedQuery>>("/queries/saved", {
      params: { project_id: projectId, ...params },
    }),

  getSavedQuery: (queryId: string) =>
    api.get<SavedQuery>(`/queries/saved/${queryId}`),

  updateSavedQuery: (queryId: string, data: UpdateQueryRequest) =>
    api.put<SavedQuery>(`/queries/saved/${queryId}`, data),

  deleteSavedQuery: (queryId: string) =>
    api.delete(`/queries/saved/${queryId}`),

  toggleQueryFavorite: (queryId: string) =>
    api.post<SavedQuery>(`/queries/saved/${queryId}/favorite`),

  toggleQueryPinned: (queryId: string) =>
    api.post<SavedQuery>(`/queries/saved/${queryId}/pin`),

  rerunSavedQuery: (queryId: string, params?: {
    page?: number;
    page_size?: number;
    enrich?: boolean;
  }) =>
    api.post<QueryResult>(`/queries/saved/${queryId}/rerun`, null, { params }),

  // ── Query History ────────────────────────────────────────────────────
  listQueryHistory: (projectId: string, params?: {
    saved_query_id?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }) =>
    api.get<PaginatedResponse<QueryHistoryEntry>>("/queries/history", {
      params: { project_id: projectId, ...params },
    }),

  getHistoryEntry: (historyId: string) =>
    api.get<QueryHistoryEntry>(`/queries/history/${historyId}`),

  deleteHistoryEntry: (historyId: string) =>
    api.delete(`/queries/history/${historyId}`),

  clearQueryHistory: (projectId: string) =>
    api.delete("/queries/history", { params: { project_id: projectId } }),

  // ── Export ────────────────────────────────────────────────────────────
  exportResults: (data: ExportRequest) =>
    api.post<ExportResult>("/queries/export", data),

  // ── Cache ─────────────────────────────────────────────────────────────
  clearQueryCache: (projectId?: string) =>
    api.delete("/queries/cache", { params: projectId ? { project_id: projectId } : undefined }),
};
