// Intelligence Analysis Engine types

export interface RegisteredModel {
  id: string;
  name: string;
  version: string;
  task: string;
  description: string | null;
  author: string | null;
  license: string | null;
  framework: string;
  input_type: string;
  output_type: string;
  weights_path: string | null;
  status: string;
  is_loaded: boolean;
  gpu_required: boolean;
  class_names_json: string | null;
  default_params_json: string | null;
  error_message: string | null;
  last_loaded_at: string | null;
  inference_count: number;
  favorite: boolean;
  archived: boolean;
  created_at: string | null;
  modified_at: string | null;
}

export interface ModelRegisterRequest {
  name: string;
  task: string;
  version?: string;
  description?: string;
  author?: string;
  license?: string;
  framework?: string;
  input_type?: string;
  output_type?: string;
  weights_path?: string;
  class_names?: string[];
  default_params?: Record<string, unknown>;
  config?: Record<string, unknown>;
  gpu_required?: boolean;
}

export interface AnalysisJob {
  id: string;
  project_id: string;
  model_id: string;
  name: string;
  description: string | null;
  task_type: string;
  status: string;
  input_path: string | null;
  input_type: string | null;
  output_path: string | null;
  progress: number;
  total_items: number;
  processed_items: number;
  detection_count: number;
  execution_time_ms: number;
  tile_size: number;
  tile_overlap: number;
  batch_size: number;
  confidence_threshold: number;
  iou_threshold: number;
  device: string;
  cancel_requested: boolean;
  error_message: string | null;
  result_asset_id: string | null;
  favorite: boolean;
  archived: boolean;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
  modified_at: string | null;
}

export interface AnalysisJobCreateRequest {
  name: string;
  model_id: string;
  input_path: string;
  description?: string;
  task_type?: string;
  input_type?: string;
  tile_size?: number;
  tile_overlap?: number;
  batch_size?: number;
  confidence_threshold?: number;
  iou_threshold?: number;
  device?: string;
  parameters?: Record<string, unknown>;
}

export interface Detection {
  id: string;
  job_id: string;
  project_id: string;
  model_id: string | null;
  class_name: string;
  class_id: number;
  confidence: number;
  geometry_json: string;
  bbox_min_x: number;
  bbox_min_y: number;
  bbox_max_x: number;
  bbox_max_y: number;
  centroid_x: number;
  centroid_y: number;
  area: number;
  model_version: string | null;
  execution_time_ms: number;
  tile_x: number | null;
  tile_y: number | null;
  review_status: string;
  reviewer_notes: string | null;
  reviewed_at: string | null;
  reviewed_by: string | null;
  edited_geometry_json: string | null;
  created_at: string | null;
}

export interface ReviewRequest {
  review_status: string;
  reviewer_notes?: string;
  reviewed_by?: string;
}

export interface BatchReviewRequest {
  detection_ids: string[];
  review_status: string;
  reviewer_notes?: string;
  reviewed_by?: string;
}

export interface IntelligenceConfig {
  task_types: string[];
  device_types: string[];
  review_status: string[];
  export_formats: string[];
}

export interface ReviewStats {
  total: number;
  pending: number;
  accepted: number;
  rejected: number;
  uncertain: number;
  by_class?: Record<string, { total: number; accepted: number; rejected: number }>;
}

export interface AnalysisHistoryEntry {
  id: string;
  job_id: string;
  action: string;
  details: string | null;
  entity_type: string | null;
  entity_id: string | null;
  timestamp: string | null;
}

export type TaskType = "detection" | "segmentation" | "classification" | "similarity_search" | "feature_extraction";
export type DeviceType = "cpu" | "cuda" | "mps";
export type ReviewStatusType = "pending" | "accepted" | "rejected" | "uncertain";
