import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { aoiApi, layerApi, importApi, exportApi } from "../services/api";
import { assetApi } from "../services/assetApi";
import { rasterApi } from "../services/rasterApi";
import type { AOICreate, AOIUpdate, LayerCreate, LayerUpdate, ExportRequest } from "../types";
import type { RasterImportResponse } from "../types/gis";

export function useProjectAssets(projectId: string | null) {
  return useQuery({
    queryKey: ["project-assets", projectId],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await assetApi.list({ project_id: projectId, limit: 500 });
      return response.data.assets;
    },
    enabled: !!projectId,
  });
}

// ============================================================
// AOI Hooks
// ============================================================

export function useAOIs(projectId: string | null) {
  return useQuery({
    queryKey: ["aois", projectId],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await aoiApi.list(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useAOI(projectId: string | null, aoiId: string | null) {
  return useQuery({
    queryKey: ["aois", projectId, aoiId],
    queryFn: async () => {
      if (!projectId || !aoiId) return null;
      const response = await aoiApi.getById(projectId, aoiId);
      return response.data;
    },
    enabled: !!projectId && !!aoiId,
  });
}

export function useCreateAOI() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      data,
    }: {
      projectId: string;
      data: AOICreate;
    }) => {
      const response = await aoiApi.create(projectId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["aois", variables.projectId] });
    },
  });
}

export function useUpdateAOI() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      aoiId,
      data,
    }: {
      projectId: string;
      aoiId: string;
      data: AOIUpdate;
    }) => {
      const response = await aoiApi.update(projectId, aoiId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["aois", variables.projectId] });
    },
  });
}

export function useDeleteAOI() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      aoiId,
    }: {
      projectId: string;
      aoiId: string;
    }) => {
      await aoiApi.delete(projectId, aoiId);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["aois", variables.projectId] });
    },
  });
}

// ============================================================
// Layer Hooks
// ============================================================

export function useLayers(projectId: string | null) {
  return useQuery({
    queryKey: ["layers", projectId],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await layerApi.list(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreateLayer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      data,
    }: {
      projectId: string;
      data: LayerCreate;
    }) => {
      const response = await layerApi.create(projectId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["layers", variables.projectId] });
    },
  });
}

export function useUpdateLayer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      layerId,
      data,
    }: {
      projectId: string;
      layerId: string;
      data: LayerUpdate;
    }) => {
      const response = await layerApi.update(projectId, layerId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["layers", variables.projectId] });
    },
  });
}

export function useToggleLayerVisibility() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      layerId,
    }: {
      projectId: string;
      layerId: string;
    }) => {
      const response = await layerApi.toggleVisibility(projectId, layerId);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["layers", variables.projectId] });
    },
  });
}

export function useDeleteLayer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      layerId,
    }: {
      projectId: string;
      layerId: string;
    }) => {
      await layerApi.delete(projectId, layerId);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["layers", variables.projectId] });
    },
  });
}

export function useReorderLayers() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      layerIds,
    }: {
      projectId: string;
      layerIds: string[];
    }) => {
      const response = await layerApi.reorder(projectId, layerIds);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["layers", variables.projectId] });
    },
  });
}

export function useLayerFeatures(projectId: string | null, layerId: string | null) {
  return useQuery({
    queryKey: ["layer-features", projectId, layerId],
    queryFn: async () => {
      if (!projectId || !layerId) return null;
      const response = await layerApi.getFeatures(projectId, layerId, {
        max_features: 2000,
        simplify: true,
      });
      return response.data;
    },
    enabled: !!projectId && !!layerId,
    staleTime: 60_000,
  });
}

export function useImportRaster() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      file,
    }: {
      projectId: string;
      file: File;
    }): Promise<RasterImportResponse> => {
      const response = await rasterApi.importRaster(projectId, file);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["layers", variables.projectId] });
    },
  });
}

export function useRegisterAssetLayer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      assetId,
      name,
    }: {
      projectId: string;
      assetId: string;
      name?: string;
    }) => {
      const response = await layerApi.fromAsset(projectId, { asset_id: assetId, name });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["layers", variables.projectId] });
    },
  });
}

// ============================================================
// Import Hooks
// ============================================================

export function useImportGeoJSON() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      file,
    }: {
      projectId: string;
      file: File;
    }) => {
      const response = await importApi.geojson(projectId, file);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["layers", variables.projectId] });
      queryClient.invalidateQueries({ queryKey: ["imported-files", variables.projectId] });
    },
  });
}

export function useImportKML() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      file,
    }: {
      projectId: string;
      file: File;
    }) => {
      const response = await importApi.kml(projectId, file);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["layers", variables.projectId] });
      queryClient.invalidateQueries({ queryKey: ["imported-files", variables.projectId] });
    },
  });
}

export function useImportShapefile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      file,
    }: {
      projectId: string;
      file: File;
    }) => {
      const response = await importApi.shapefile(projectId, file);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["layers", variables.projectId] });
      queryClient.invalidateQueries({ queryKey: ["imported-files", variables.projectId] });
    },
  });
}

// ============================================================
// Export Hooks
// ============================================================

export function useExportGeoJSON() {
  return useMutation({
    mutationFn: async ({
      projectId,
      data,
    }: {
      projectId: string;
      data: ExportRequest;
    }) => {
      const response = await exportApi.geojson(projectId, data);
      return response.data;
    },
  });
}

export function useExportKML() {
  return useMutation({
    mutationFn: async ({
      projectId,
      data,
    }: {
      projectId: string;
      data: ExportRequest;
    }) => {
      const response = await exportApi.kml(projectId, data);
      return response.data;
    },
  });
}


