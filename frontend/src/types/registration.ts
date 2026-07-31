export interface ImageRegistration {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  reference_path: string;
  target_path: string;
  output_path: string | null;
  mode: string;
  feature_detector: string;
  feature_matcher: string;
  transform_type: string;
  resampling: string;
  status: string;
  error_message: string | null;
  ref_width: number | null;
  ref_height: number | null;
  ref_crs: string | null;
  ref_resolution: string | null;
  tgt_width: number | null;
  tgt_height: number | null;
  tgt_crs: string | null;
  tgt_resolution: string | null;
  transform_matrix: number[][] | null;
  rmse: number | null;
  matched_points: number | null;
  inlier_count: number | null;
  inlier_ratio: number | null;
  confidence_score: number | null;
  pipeline_id: string | null;
  favorite: boolean;
  archived: boolean;
  created_at: string | null;
  updated_at: string | null;
  completed_at: string | null;
}

export interface ControlPoint {
  id: string;
  registration_id: string;
  point_index: number;
  ref_x: number;
  ref_y: number;
  target_x: number;
  target_y: number;
  ref_lon: number | null;
  ref_lat: number | null;
  target_lon: number | null;
  target_lat: number | null;
  residual: number | null;
  is_inlier: boolean;
  label: string | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface RegistrationHistory {
  id: string;
  registration_id: string;
  operation: string;
  status: string;
  parameters: string | null;
  error_message: string | null;
  execution_time_ms: number | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface RegistrationMetrics {
  id: string;
  registration_id: string;
  features_detected_ref: number | null;
  features_detected_tgt: number | null;
  raw_matches: number | null;
  good_matches: number | null;
  inlier_matches: number | null;
  transform_determinant: number | null;
  max_residual: number | null;
  median_residual: number | null;
  overall_score: number | null;
  quality_grade: string | null;
  raw_metrics: string | null;
  created_at: string | null;
}

export interface RegistrationConfig {
  feature_detectors: Record<string, string>;
  feature_matchers: Record<string, string>;
  transform_types: Record<string, string>;
  resampling_methods: Record<string, string>;
  registration_modes: Record<string, string>;
}

export interface RegistrationCreateRequest {
  name: string;
  description?: string;
  reference_path: string;
  target_path: string;
  mode?: string;
  feature_detector?: string;
  feature_matcher?: string;
  transform_type?: string;
  resampling?: string;
}

export interface ControlPointCreateRequest {
  ref_x: number;
  ref_y: number;
  target_x: number;
  target_y: number;
  ref_lon?: number;
  ref_lat?: number;
  target_lon?: number;
  target_lat?: number;
  label?: string;
  notes?: string;
}

export interface ControlPointMoveRequest {
  ref_x: number;
  ref_y: number;
  target_x: number;
  target_y: number;
}
