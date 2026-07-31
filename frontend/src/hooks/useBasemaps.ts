import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { basemapApi } from "../services/api";
import type { GisBasemap } from "../types/gis";
import { BLANK_GRID_ID } from "../types/gis";

export function useBasemaps() {
  return useQuery({
    queryKey: ["basemaps"],
    queryFn: async () => {
      const response = await basemapApi.list();
      return response.data;
    },
  });
}

export function useRegisterGeotiffBasemap() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; path: string }) =>
      basemapApi.registerGeotiff(data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["basemaps"] });
    },
  });
}

export function useDeleteBasemap() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (basemapId: string) => basemapApi.delete(basemapId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["basemaps"] });
    },
  });
}

export function resolveBasemap(
  basemapId: string | undefined | null,
  basemaps: GisBasemap[] | undefined
): GisBasemap | undefined {
  if (!basemapId) return undefined;
  const found = basemaps?.find((b) => b.id === basemapId);
  if (found) return found;
  if (basemapId === BLANK_GRID_ID) {
    return {
      id: BLANK_GRID_ID,
      name: "Blank Grid",
      basemap_type: "blank",
      crs: "EPSG:3857",
      tile_url_template: "",
    };
  }
  return undefined;
}
