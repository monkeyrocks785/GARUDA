import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { queryApi } from "../services/queryApi";
import type {
  QueryRequest,
  SaveQueryRequest,
  UpdateQueryRequest,
  ExportRequest,
} from "../types/query";

// ── Config ──────────────────────────────────────────────────────────────────

export function useQueryConfig() {
  return useQuery({
    queryKey: ["queryConfig"],
    queryFn: async () => {
      const response = await queryApi.getConfig();
      return response.data;
    },
  });
}

// ── Query Execution ─────────────────────────────────────────────────────────

export function useExecuteQuery() {
  return useMutation({
    mutationFn: async ({
      data,
      useCache,
    }: {
      data: QueryRequest;
      useCache?: boolean;
    }) => {
      const response = await queryApi.executeQuery(data, useCache);
      return response.data;
    },
  });
}

export function useExecuteRawQuery() {
  return useMutation({
    mutationFn: async ({
      filters,
      projectId,
      page,
      pageSize,
      enrich,
    }: {
      filters: Record<string, unknown>;
      projectId: string;
      page?: number;
      pageSize?: number;
      enrich?: boolean;
    }) => {
      const response = await queryApi.executeRawQuery(
        filters, projectId, page, pageSize, enrich,
      );
      return response.data;
    },
  });
}

// ── Saved Queries ───────────────────────────────────────────────────────────

export function useSavedQueries(
  projectId: string | null,
  params?: { favorite_only?: boolean; pinned_only?: boolean; search?: string; page?: number; page_size?: number },
) {
  return useQuery({
    queryKey: ["savedQueries", projectId, params],
    queryFn: async () => {
      if (!projectId) return { items: [], total: 0, page: 0, page_size: 50 };
      const response = await queryApi.listSavedQueries(projectId, params);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useSavedQuery(queryId: string | null) {
  return useQuery({
    queryKey: ["savedQuery", queryId],
    queryFn: async () => {
      if (!queryId) return null;
      const response = await queryApi.getSavedQuery(queryId);
      return response.data;
    },
    enabled: !!queryId,
  });
}

export function useSaveQuery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SaveQueryRequest) => {
      const response = await queryApi.saveQuery(data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["savedQueries", data.project_id] });
    },
  });
}

export function useUpdateSavedQuery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      queryId,
      data,
      projectId: _projectId,
    }: {
      queryId: string;
      data: UpdateQueryRequest;
      projectId: string;
    }) => {
      const response = await queryApi.updateSavedQuery(queryId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["savedQueries", variables.projectId] });
      queryClient.invalidateQueries({ queryKey: ["savedQuery", variables.queryId] });
    },
  });
}

export function useDeleteSavedQuery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ queryId, projectId: _projectId }: { queryId: string; projectId: string }) => {
      await queryApi.deleteSavedQuery(queryId);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["savedQueries", variables.projectId] });
    },
  });
}

export function useToggleQueryFavorite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (queryId: string) => {
      const response = await queryApi.toggleQueryFavorite(queryId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["savedQueries"] });
      queryClient.invalidateQueries({ queryKey: ["savedQuery"] });
    },
  });
}

export function useToggleQueryPinned() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (queryId: string) => {
      const response = await queryApi.toggleQueryPinned(queryId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["savedQueries"] });
      queryClient.invalidateQueries({ queryKey: ["savedQuery"] });
    },
  });
}

export function useRerunSavedQuery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      queryId,
      page,
      pageSize,
      enrich,
    }: {
      queryId: string;
      page?: number;
      pageSize?: number;
      enrich?: boolean;
    }) => {
      const response = await queryApi.rerunSavedQuery(queryId, { page, page_size: pageSize, enrich });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["queryHistory"] });
    },
  });
}

// ── Query History ───────────────────────────────────────────────────────────

export function useQueryHistory(
  projectId: string | null,
  params?: { saved_query_id?: string; status?: string; page?: number; page_size?: number },
) {
  return useQuery({
    queryKey: ["queryHistory", projectId, params],
    queryFn: async () => {
      if (!projectId) return { items: [], total: 0, page: 0, page_size: 50 };
      const response = await queryApi.listQueryHistory(projectId, params);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useDeleteHistoryEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ historyId, projectId: _projectId }: { historyId: string; projectId: string }) => {
      await queryApi.deleteHistoryEntry(historyId);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["queryHistory", variables.projectId] });
    },
  });
}

export function useClearQueryHistory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projectId: string) => {
      await queryApi.clearQueryHistory(projectId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["queryHistory"] });
    },
  });
}

// ── Export ──────────────────────────────────────────────────────────────────

export function useExportResults() {
  return useMutation({
    mutationFn: async (data: ExportRequest) => {
      const response = await queryApi.exportResults(data);
      return response.data;
    },
  });
}

// ── Cache ───────────────────────────────────────────────────────────────────

export function useClearQueryCache() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projectId?: string) => {
      await queryApi.clearQueryCache(projectId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["queryHistory"] });
    },
  });
}
