import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assetApi } from "../services/assetApi";
import { useAssetStore } from "../store/useAssetStore";

export function useAssets() {
  const {
    projectId, searchQuery, filterType, filterCategory,
    filterTags, showFavoritesOnly, showArchived, sortBy, sortOrder,
  } = useAssetStore();

  return useQuery({
    queryKey: [
      "assets", projectId, searchQuery, filterType, filterCategory,
      filterTags, showFavoritesOnly, showArchived, sortBy, sortOrder,
    ],
    queryFn: () =>
      assetApi.list({
        project_id: projectId || undefined,
        query: searchQuery || undefined,
        asset_type: filterType || undefined,
        category: filterCategory || undefined,
        tags: filterTags.length > 0 ? filterTags.join(",") : undefined,
        favorite_only: showFavoritesOnly,
        sort_by: sortBy,
        sort_order: sortOrder,
      }).then((r) => r.data),
  });
}

export function useAsset(assetId: string | null) {
  return useQuery({
    queryKey: ["asset", assetId],
    queryFn: () => assetApi.get(assetId!).then((r) => r.data),
    enabled: !!assetId,
  });
}

export function useAssetStats() {
  const { projectId } = useAssetStore();
  return useQuery({
    queryKey: ["assetStats", projectId],
    queryFn: () => assetApi.getStats(projectId!).then((r) => r.data),
    enabled: !!projectId,
  });
}

export function useAssetHistory(assetId: string | null) {
  return useQuery({
    queryKey: ["assetHistory", assetId],
    queryFn: () => assetApi.getHistory(assetId!).then((r) => r.data),
    enabled: !!assetId,
  });
}

export function useAssetRelated(assetId: string | null) {
  return useQuery({
    queryKey: ["assetRelated", assetId],
    queryFn: () => assetApi.getRelated(assetId!).then((r) => r.data),
    enabled: !!assetId,
  });
}

export function useCollections() {
  const { projectId } = useAssetStore();
  return useQuery({
    queryKey: ["collections", projectId],
    queryFn: () => assetApi.listCollections(projectId || undefined).then((r) => r.data),
  });
}

export function useCollectionAssets(collectionId: string | null) {
  return useQuery({
    queryKey: ["collectionAssets", collectionId],
    queryFn: () => assetApi.getCollectionAssets(collectionId!).then((r) => r.data),
    enabled: !!collectionId,
  });
}

export function useImportAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, options }: { file: File; options?: Record<string, string> }) =>
      assetApi.importFile(file, options).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      queryClient.invalidateQueries({ queryKey: ["assetStats"] });
    },
  });
}

export function useUpdateAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, string> }) =>
      assetApi.update(id, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useDeleteAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => assetApi.delete(id).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      queryClient.invalidateQueries({ queryKey: ["assetStats"] });
    },
  });
}

export function useToggleFavorite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => assetApi.toggleFavorite(id).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useTogglePin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => assetApi.togglePin(id).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useArchiveAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => assetApi.archive(id).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useRestoreAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => assetApi.restore(id).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets"] });
    },
  });
}

export function useCreateCollection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string; project_id?: string }) =>
      assetApi.createCollection(data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}

export function useAddToCollection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ collectionId, assetId }: { collectionId: string; assetId: string }) =>
      assetApi.addToCollection(collectionId, assetId).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] });
    },
  });
}
