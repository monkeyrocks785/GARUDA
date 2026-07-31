import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { projectApi } from "../services/api";
import type { ProjectCreate, ProjectUpdate } from "../types";

// ============================================================
// Query Hooks
// ============================================================

export function useProjects(params?: {
  include_archived?: boolean;
  search?: string;
  offset?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["projects", params],
    queryFn: async () => {
      const response = await projectApi.list(params);
      return response.data;
    },
  });
}

export function useProject(id: string | null) {
  return useQuery({
    queryKey: ["projects", id],
    queryFn: async () => {
      if (!id) return null;
      const response = await projectApi.getById(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useRecentProjects(limit = 10) {
  return useQuery({
    queryKey: ["projects", "recent", limit],
    queryFn: async () => {
      const response = await projectApi.getRecent(limit);
      return response.data;
    },
  });
}

export function useFavoriteProjects(limit = 50) {
  return useQuery({
    queryKey: ["projects", "favorites", limit],
    queryFn: async () => {
      const response = await projectApi.getFavorites(limit);
      return response.data;
    },
  });
}

export function useProjectStats() {
  return useQuery({
    queryKey: ["projects", "stats"],
    queryFn: async () => {
      const response = await projectApi.getStats();
      return response.data;
    },
  });
}

export function useRecoveryCheck() {
  return useQuery({
    queryKey: ["projects", "recovery"],
    queryFn: async () => {
      const response = await projectApi.checkRecovery();
      return response.data;
    },
    enabled: false, // Don't auto-fetch, trigger manually
  });
}

// ============================================================
// Mutation Hooks
// ============================================================

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ProjectCreate) => {
      const response = await projectApi.create(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ProjectUpdate }) => {
      const response = await projectApi.update(id, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["projects", variables.id] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      deleteFiles = true,
    }: {
      id: string;
      deleteFiles?: boolean;
    }) => {
      await projectApi.delete(id, deleteFiles);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useArchiveProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await projectApi.archive(id);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUnarchiveProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await projectApi.unarchive(id);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useToggleFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await projectApi.toggleFavorite(id);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDuplicateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, newName }: { id: string; newName?: string }) => {
      const response = await projectApi.duplicate(id, newName);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useOpenProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await projectApi.open(id);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
