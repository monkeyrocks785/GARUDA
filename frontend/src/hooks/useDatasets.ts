import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { datasetApi } from "../services/datasetApi";
import { useDatasetStore } from "../store/useDatasetStore";

export function useDatasets() {
  const {
    projectId,
    searchQuery,
    filterType,
    filterExtension,
    filterTags,
    showFavoritesOnly,
    sortBy,
    sortOrder,
  } = useDatasetStore();

  return useQuery({
    queryKey: [
      "datasets",
      projectId,
      searchQuery,
      filterType,
      filterExtension,
      filterTags,
      showFavoritesOnly,
      sortBy,
      sortOrder,
    ],
    queryFn: () =>
      datasetApi.list(projectId!, {
        query: searchQuery || undefined,
        dataset_type: filterType || undefined,
        extension: filterExtension || undefined,
        tags: filterTags.length > 0 ? filterTags.join(",") : undefined,
        favorite_only: showFavoritesOnly,
        sort_by: sortBy,
        sort_order: sortOrder,
      }).then((r) => r.data),
    enabled: !!projectId,
  });
}

export function useDataset(datasetId: string | null) {
  return useQuery({
    queryKey: ["dataset", datasetId],
    queryFn: () => datasetApi.get(datasetId!).then((r) => r.data),
    enabled: !!datasetId,
  });
}

export function useDatasetStats() {
  const { projectId } = useDatasetStore();
  return useQuery({
    queryKey: ["datasetStats", projectId],
    queryFn: () => datasetApi.getStats(projectId!).then((r) => r.data),
    enabled: !!projectId,
  });
}

export function useDatasetVersions(datasetId: string | null) {
  return useQuery({
    queryKey: ["datasetVersions", datasetId],
    queryFn: () => datasetApi.getVersions(datasetId!).then((r) => r.data),
    enabled: !!datasetId,
  });
}

export function useDatasetMetadata(datasetId: string | null) {
  return useQuery({
    queryKey: ["datasetMetadata", datasetId],
    queryFn: () => datasetApi.getMetadata(datasetId!).then((r) => r.data),
    enabled: !!datasetId,
  });
}

export function useImportDataset() {
  const queryClient = useQueryClient();
  const { projectId } = useDatasetStore();

  return useMutation({
    mutationFn: ({ file, options }: { file: File; options?: { name?: string; description?: string; tags?: string } }) =>
      datasetApi.importFile(projectId!, file, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      queryClient.invalidateQueries({ queryKey: ["datasetStats"] });
    },
  });
}

export function useImportFolder() {
  const queryClient = useQueryClient();
  const { projectId } = useDatasetStore();

  return useMutation({
    mutationFn: ({ folderPath, recursive }: { folderPath: string; recursive?: boolean }) =>
      datasetApi.importFolder(projectId!, folderPath, recursive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      queryClient.invalidateQueries({ queryKey: ["datasetStats"] });
    },
  });
}

export function useUpdateDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string; description?: string; notes?: string } }) =>
      datasetApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}

export function useDeleteDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => datasetApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      queryClient.invalidateQueries({ queryKey: ["datasetStats"] });
    },
  });
}

export function useToggleFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => datasetApi.toggleFavorite(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}

export function useAddTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, tag }: { id: string; tag: string }) => datasetApi.addTag(id, tag),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}

export function useRemoveTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, tag }: { id: string; tag: string }) => datasetApi.removeTag(id, tag),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
  });
}
