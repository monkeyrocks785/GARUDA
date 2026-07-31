import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { rasterApi } from "../services/rasterApi";
import type {
  RasterReprojectRequest,
  RasterCropRequest,
  RasterClipRequest,
  RasterResampleRequest,
  RasterBandsRequest,
  RasterNodataRequest,
  RasterOverviewRequest,
  RasterMosaicRequest,
} from "../types/raster";

export function useRasterList(projectId: string | null) {
  return useQuery({
    queryKey: ["rasters", projectId],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await rasterApi.list(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useRaster(projectId: string | null, rasterId: string | null) {
  return useQuery({
    queryKey: ["raster", projectId, rasterId],
    queryFn: async () => {
      if (!projectId || !rasterId) return null;
      const response = await rasterApi.get(projectId, rasterId);
      return response.data;
    },
    enabled: !!projectId && !!rasterId,
  });
}

export function useExtractMetadata() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      filePath,
      datasetId,
    }: {
      projectId: string;
      filePath: string;
      datasetId?: string;
    }) => {
      const response = await rasterApi.extractMetadata(projectId, filePath, datasetId);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["rasters", variables.projectId],
      });
    },
  });
}

export function useReprojectRaster() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      rasterId,
      data,
    }: {
      projectId: string;
      rasterId: string;
      data: RasterReprojectRequest;
    }) => {
      const response = await rasterApi.reproject(projectId, rasterId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["rasters", variables.projectId],
      });
    },
  });
}

export function useCropRaster() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      rasterId,
      data,
    }: {
      projectId: string;
      rasterId: string;
      data: RasterCropRequest;
    }) => {
      const response = await rasterApi.crop(projectId, rasterId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["rasters", variables.projectId],
      });
    },
  });
}

export function useClipRaster() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      rasterId,
      data,
    }: {
      projectId: string;
      rasterId: string;
      data: RasterClipRequest;
    }) => {
      const response = await rasterApi.clip(projectId, rasterId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["rasters", variables.projectId],
      });
    },
  });
}

export function useResampleRaster() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      rasterId,
      data,
    }: {
      projectId: string;
      rasterId: string;
      data: RasterResampleRequest;
    }) => {
      const response = await rasterApi.resample(projectId, rasterId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["rasters", variables.projectId],
      });
    },
  });
}

export function useExtractBands() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      rasterId,
      data,
    }: {
      projectId: string;
      rasterId: string;
      data: RasterBandsRequest;
    }) => {
      const response = await rasterApi.extractBands(projectId, rasterId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["rasters", variables.projectId],
      });
    },
  });
}

export function useSetNodata() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      rasterId,
      data,
    }: {
      projectId: string;
      rasterId: string;
      data: RasterNodataRequest;
    }) => {
      const response = await rasterApi.setNodata(projectId, rasterId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["rasters", variables.projectId],
      });
    },
  });
}

export function useCreateOverview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      rasterId,
      data,
    }: {
      projectId: string;
      rasterId: string;
      data: RasterOverviewRequest;
    }) => {
      const response = await rasterApi.createOverview(projectId, rasterId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["rasters", variables.projectId],
      });
    },
  });
}

export function useRasterHistory(projectId: string | null) {
  return useQuery({
    queryKey: ["rasterHistory", projectId],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await rasterApi.getHistory(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useRasterDerived(projectId: string | null) {
  return useQuery({
    queryKey: ["rasterDerived", projectId],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await rasterApi.getDerived(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useMosaicRasters() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      data,
    }: {
      projectId: string;
      data: RasterMosaicRequest;
    }) => {
      const response = await rasterApi.mosaic(projectId, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["rasters", variables.projectId],
      });
    },
  });
}
