import api from "./api";
import type {
  RasterMetadata,
  RasterReprojectRequest,
  RasterCropRequest,
  RasterClipRequest,
  RasterResampleRequest,
  RasterBandsRequest,
  RasterNodataRequest,
  RasterOverviewRequest,
  RasterMosaicRequest,
  RasterProcessingResult,
  RasterProcessingHistory,
  RasterDerivedProduct,
  RasterThumbnail,
} from "../types/raster";
import type { RasterImportResponse } from "../types/gis";

export const rasterApi = {
  importRaster: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<RasterImportResponse>(
      `/rasters/${projectId}/import`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
  },

  extractMetadata: (projectId: string, filePath: string, datasetId?: string) =>
    api.post<RasterMetadata>(
      `/rasters/${projectId}/metadata`,
      null,
      { params: { file_path: filePath, dataset_id: datasetId } }
    ),

  list: (projectId: string) =>
    api.get<RasterMetadata[]>(`/rasters/${projectId}/list`),

  get: (projectId: string, rasterId: string) =>
    api.get<RasterMetadata>(`/rasters/${projectId}/${rasterId}`),

  reproject: (projectId: string, rasterId: string, data: RasterReprojectRequest) =>
    api.post<RasterProcessingResult>(
      `/rasters/${projectId}/${rasterId}/reproject`,
      data
    ),

  crop: (projectId: string, rasterId: string, data: RasterCropRequest) =>
    api.post<RasterProcessingResult>(
      `/rasters/${projectId}/${rasterId}/crop`,
      data
    ),

  clip: (projectId: string, rasterId: string, data: RasterClipRequest) =>
    api.post<RasterProcessingResult>(
      `/rasters/${projectId}/${rasterId}/clip`,
      data
    ),

  resample: (projectId: string, rasterId: string, data: RasterResampleRequest) =>
    api.post<RasterProcessingResult>(
      `/rasters/${projectId}/${rasterId}/resample`,
      data
    ),

  extractBands: (projectId: string, rasterId: string, data: RasterBandsRequest) =>
    api.post<RasterProcessingResult>(
      `/rasters/${projectId}/${rasterId}/bands`,
      data
    ),

  setNodata: (projectId: string, rasterId: string, data: RasterNodataRequest) =>
    api.post<RasterProcessingResult>(
      `/rasters/${projectId}/${rasterId}/nodata`,
      data
    ),

  createOverview: (projectId: string, rasterId: string, data: RasterOverviewRequest) =>
    api.post<RasterProcessingResult>(
      `/rasters/${projectId}/${rasterId}/overview`,
      data
    ),

  generateThumbnail: (projectId: string, rasterId: string, width?: number, height?: number) =>
    api.post<RasterThumbnail>(
      `/rasters/${projectId}/${rasterId}/thumbnail`,
      null,
      { params: { width: width || 256, height: height || 256 } }
    ),

  mosaic: (projectId: string, data: RasterMosaicRequest) =>
    api.post<RasterProcessingResult>(
      `/rasters/${projectId}/mosaic`,
      data
    ),

  getHistory: (projectId: string) =>
    api.get<RasterProcessingHistory[]>(`/rasters/${projectId}/history`),

  getDerived: (projectId: string) =>
    api.get<RasterDerivedProduct[]>(`/rasters/${projectId}/derived`),
};
