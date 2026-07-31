// eslint-disable-next-line @typescript-eslint/no-namespace
declare namespace GeoJSON {
  interface Geometry {
    type: string;
    coordinates: number[] | number[][] | number[][][] | number[][][][];
  }
  interface Feature {
    type: "Feature";
    geometry: Geometry;
    properties: Record<string, unknown> | null;
  }
  interface FeatureCollection {
    type: "FeatureCollection";
    features: Feature[];
  }
}

export interface Health {
  status: string;
  version: string;
  uptime: string;
  environment: string;
  timestamp: string;
}

export interface DetailedHealth {
  status: string;
  database: string;
  timestamp: string;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  status: string;
  current_stage: string | null;
  current_task: string | null;
  progress: number;
  area_of_interest: string | null;
  coordinate_system: string | null;
  storage_path: string;
  tags: string | null;
  notes: string | null;
  favorite: boolean;
  archived: boolean;
  completed_steps: string | null;
  pending_steps: string | null;
  last_opened_file: string | null;
  last_viewed_map_position: string | null;
  selected_layers: string | null;
  dashboard_layout: string | null;
  user_notes: string | null;
  is_processing: boolean;
  last_job_id: string | null;
  last_job_status: string | null;
  project_version: string;
  created_at: string;
  updated_at: string;
  last_opened_at: string | null;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  area_of_interest?: string;
  coordinate_system?: string;
  tags?: string[];
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  area_of_interest?: string;
  coordinate_system?: string;
  tags?: string[];
  notes?: string;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
  offset: number;
  limit: number;
}

export interface ProjectStats {
  total: number;
  archived: number;
  favorites: number;
  processing: number;
}

export interface RecoveryResponse {
  recovered: Project[];
  count: number;
}

export type ProjectStatus =
  | "created"
  | "active"
  | "processing"
  | "completed"
  | "failed"
  | "archived";

export type ProjectStage =
  | "initialization"
  | "data_acquisition"
  | "processing"
  | "analysis"
  | "reporting";

// ============================================================
// AOI Types
// ============================================================

export interface AOI {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  geometry: string;
  geometry_type: string;
  bbox: string | null;
  area_m2: number | null;
  fill_color: string;
  fill_opacity: number;
  stroke_color: string;
  stroke_width: number;
  source: string;
  source_file: string | null;
  created_at: string;
  updated_at: string;
}

export interface AOICreate {
  name: string;
  description?: string;
  geometry: GeoJSON.Geometry;
  fill_color?: string;
  fill_opacity?: number;
  stroke_color?: string;
  stroke_width?: number;
}

export interface AOIUpdate {
  name?: string;
  description?: string;
  geometry?: GeoJSON.Geometry;
  fill_color?: string;
  fill_opacity?: number;
  stroke_color?: string;
  stroke_width?: number;
}

// ============================================================
// Layer Types
// ============================================================

export interface Layer {
  id: string;
  project_id: string;
  name: string;
  layer_type: string;
  visible: boolean;
  opacity: number;
  z_index: number;
  source_id: string | null;
  source_type: string | null;
  style: string | null;
  metadata: string | null;
  created_at: string;
  updated_at: string;
}

export interface LayerCreate {
  name: string;
  layer_type: string;
  source_id?: string;
  source_type?: string;
  style?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  z_index?: number;
}

export interface LayerUpdate {
  name?: string;
  visible?: boolean;
  opacity?: number;
  z_index?: number;
  style?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

// ============================================================
// Imported File Types
// ============================================================

export interface ImportedFile {
  id: string;
  project_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  storage_path: string;
  geometry_type: string | null;
  feature_count: number;
  is_valid: boolean;
  validation_errors: string | null;
  layer_id: string | null;
  created_at: string;
}

export interface ImportResponse {
  file_id: string;
  layer_id: string;
  filename: string;
  file_type: string;
  feature_count: number;
  geometry_type: string | null;
}

// ============================================================
// Export Types
// ============================================================

export interface ExportRequest {
  aoi_ids: string[];
  geometry_ids?: string[];
  name?: string;
}

export interface ExportResponse {
  content: string;
  filename: string;
  format: string;
}

// ============================================================
// Basemap Types
// ============================================================

export interface BasemapOption {
  id: string;
  name: string;
  url: string;
  attribution: string;
}

export const BASEMAPS: BasemapOption[] = [
  {
    id: "osm",
    name: "OpenStreetMap",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  },
  {
    id: "esri_satellite",
    name: "ESRI Satellite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; Esri, Maxar, Earthstar Geographics',
  },
  {
    id: "esri_terrain",
    name: "ESRI Terrain",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; Esri',
  },
  {
    id: "esri_topographic",
    name: "ESRI Topographic",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; Esri',
  },
  {
    id: "carto_light",
    name: "Carto Light",
    url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; CARTO',
  },
  {
    id: "carto_dark",
    name: "Carto Dark",
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution: '&copy; CARTO',
  },
];

// ============================================================
// Map Tool Types
// ============================================================

export type MapTool =
  | "pan"
  | "zoom"
  | "home"
  | "measure_distance"
  | "measure_area"
  | "draw_polygon"
  | "draw_rectangle"
  | "draw_circle"
  | "delete_shape"
  | "edit_shape"
  | "coordinate_picker";

export interface MapToolOption {
  id: MapTool;
  name: string;
  icon: string;
  description: string;
}

export const MAP_TOOLS: MapToolOption[] = [
  { id: "pan", name: "Pan", icon: "🖐️", description: "Pan the map" },
  { id: "zoom", name: "Zoom", icon: "🔍", description: "Zoom in/out" },
  { id: "home", name: "Home", icon: "🏠", description: "Reset view" },
  { id: "measure_distance", name: "Measure Distance", icon: "📏", description: "Measure distance" },
  { id: "measure_area", name: "Measure Area", icon: "📐", description: "Measure area" },
  { id: "draw_polygon", name: "Draw Polygon", icon: "pentagon", description: "Draw polygon" },
  { id: "draw_rectangle", name: "Draw Rectangle", icon: "⬜", description: "Draw rectangle" },
  { id: "draw_circle", name: "Draw Circle", icon: "⭕", description: "Draw circle" },
  { id: "delete_shape", name: "Delete Shape", icon: "🗑️", description: "Delete shape" },
  { id: "edit_shape", name: "Edit Shape", icon: "✏️", description: "Edit shape" },
  { id: "coordinate_picker", name: "Coordinate Picker", icon: "📍", description: "Pick coordinates" },
];
