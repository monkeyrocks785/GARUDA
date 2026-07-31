export interface Dataset {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  dataset_type: string;
  original_filename: string;
  extension: string;
  coordinate_system: string | null;
  bbox_min_x: number | null;
  bbox_min_y: number | null;
  bbox_max_x: number | null;
  bbox_max_y: number | null;
  resolution_x: number | null;
  resolution_y: number | null;
  bands: number | null;
  width: number | null;
  height: number | null;
  file_size: number;
  checksum: string;
  status: string;
  version: number;
  is_favorite: boolean;
  is_archived: boolean;
  source: string | null;
  storage_path: string;
  tags: string | null;
  notes: string | null;
  created_at: string;
  modified_at: string;
  imported_at: string;
}

export interface DatasetCreate {
  name?: string;
  description?: string;
  tags?: string[];
}

export interface DatasetUpdate {
  name?: string;
  description?: string;
  notes?: string;
}

export interface DatasetListResponse {
  datasets: Dataset[];
  total: number;
  offset: number;
  limit: number;
}

export interface DatasetStats {
  total: number;
  by_type: Record<string, number>;
  by_extension: Record<string, number>;
  total_size_bytes: number;
}

export interface DatasetVersion {
  id: string;
  version_number: number;
  checksum: string;
  file_size: number;
  change_description: string;
  created_at: string | null;
}

export interface ImportResult {
  success: boolean;
  dataset_id: string | null;
  version: number;
  is_duplicate: boolean;
  is_new_version: boolean;
  errors: string[];
  warnings: string[];
}

export interface ImportMultipleResult {
  results: ImportResult[];
  total: number;
  imported: number;
  duplicates: number;
  errors: number;
}

export const DATASET_TYPES = [
  "raster",
  "vector",
  "image",
  "tabular",
  "laser",
  "video",
  "sar",
  "drone",
  "other",
] as const;

export const DATASET_TYPE_ICONS: Record<string, string> = {
  raster: "R",
  vector: "V",
  image: "I",
  tabular: "T",
  laser: "L",
  video: "VD",
  sar: "S",
  drone: "D",
  other: "O",
};
