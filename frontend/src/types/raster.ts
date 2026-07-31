export interface RasterMetadata {
  id: string;
  dataset_id: string | null;
  project_id: string;
  file_path: string;
  width: number;
  height: number;
  band_count: number;
  data_type: string;
  nodata_value: number | null;
  crs: string;
  resolution_x: number;
  resolution_y: number;
  bounds_min_x: number;
  bounds_min_y: number;
  bounds_max_x: number;
  bounds_max_y: number;
  file_format: string;
  file_size: number;
  has_overviews: boolean;
  compression: string | null;
  statistics: string | null;
  histogram: string | null;
  created_at: string;
  updated_at: string;
}

export interface RasterReprojectRequest {
  target_crs: string;
  resampling?: string;
}

export interface RasterCropRequest {
  bbox: [number, number, number, number];
}

export interface RasterClipRequest {
  geometry: { type: string; coordinates: unknown };
  all_touched?: boolean;
}

export interface RasterResampleRequest {
  target_width?: number;
  target_height?: number;
  target_resolution?: [number, number];
  resampling?: string;
}

export interface RasterBandsRequest {
  bands: number[];
}

export interface RasterNodataRequest {
  operation: "set" | "fill";
  nodata_value?: number;
  fill_value?: number;
  use_interpolation?: boolean;
}

export interface RasterOverviewRequest {
  levels?: number[];
  resampling?: string;
}

export interface RasterMosaicRequest {
  file_paths: string[];
  output_filename?: string;
  method?: string;
}

export interface RasterProcessingResult {
  source_crs?: string;
  target_crs?: string;
  width?: number;
  height?: number;
  resampling?: string;
  levels?: number[];
  input_count?: number;
  nodata_value?: number;
  original_size?: [number, number];
  new_size?: [number, number];
  extracted_bands?: number[];
  output_bands?: number;
}

export interface RasterProcessingHistory {
  id: string;
  operation: string;
  status: string;
  input_path: string | null;
  output_path: string | null;
  error_message: string | null;
  execution_time_ms: number | null;
  created_at: string | null;
}

export interface RasterDerivedProduct {
  id: string;
  source_dataset_id: string;
  operation: string;
  output_path: string;
  output_filename: string;
  file_size: number;
  created_at: string | null;
}

export interface RasterThumbnail {
  width: number;
  height: number;
  format: string;
}
