export interface Asset {
  id: string;
  project_id: string | null;
  name: string;
  display_name: string | null;
  description: string | null;
  asset_type: string;
  category: string | null;
  extension: string;
  storage_path: string;
  preview_path: string | null;
  thumbnail_path: string | null;
  file_size: number;
  checksum: string;
  owner: string | null;
  status: string;
  version: number;
  is_favorite: boolean;
  is_pinned: boolean;
  is_archived: boolean;
  is_hidden: boolean;
  tags: string | null;
  created_at: string;
  modified_at: string;
  imported_at: string | null;
  last_opened_at: string | null;
  last_used_at: string | null;
}

export interface AssetListResponse {
  assets: Asset[];
  total: number;
  offset: number;
  limit: number;
}

export interface AssetStats {
  total: number;
  by_type: Record<string, number>;
  by_category: Record<string, number>;
  total_size_bytes: number;
}

export interface Collection {
  id: string;
  name: string;
  description: string | null;
  project_id: string | null;
  color: string | null;
  icon: string | null;
  created_at: string;
}

export interface AssetHistory {
  id: string;
  action: string;
  details: string | null;
  performed_by: string | null;
  timestamp: string;
}

export interface AssetRelationship {
  asset: Asset;
  relationship_type: string;
  direction: string;
  relationship_id: string;
}

export const ASSET_TYPES = [
  "raster", "vector", "terrain", "document", "spreadsheet",
  "video", "audio", "image", "report", "model",
  "configuration", "log", "pipeline_result", "temporary", "other",
] as const;

export const ASSET_CATEGORIES = [
  "satellite", "drone", "survey", "analysis", "report",
  "model", "configuration", "data", "output", "archive", "system",
] as const;

export const ASSET_TYPE_ICONS: Record<string, string> = {
  raster: "R", vector: "V", terrain: "T", document: "D",
  spreadsheet: "S", video: "VD", audio: "A", image: "I",
  report: "RP", model: "M", configuration: "C", log: "L",
  pipeline_result: "P", temporary: "TMP", other: "O",
};
