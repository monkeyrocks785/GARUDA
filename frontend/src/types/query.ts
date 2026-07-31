// Intelligence Query Engine types

export interface QueryConfig {
  entity_types: string[];
  event_types: string[];
  relationship_types: string[];
  spatial_operators: string[];
  temporal_operators: string[];
  review_statuses: string[];
  sort_directions: string[];
  export_formats: string[];
  result_view_modes: string[];
}

export interface SpatialFilter {
  operator: string;
  geometry?: Record<string, unknown>;
  aoi_id?: string;
  buffer_meters?: number;
  distance_meters?: number;
  nearest_count?: number;
  bbox?: number[];
}

export interface TemporalFilter {
  operator: string;
  date?: string;
  date_from?: string;
  date_to?: string;
  min_observations?: number;
  max_observations?: number;
  min_duration_days?: number;
  max_duration_days?: number;
}

export interface RelationshipFilter {
  relationship_type: string;
  target_entity_id?: string;
  target_entity_type?: string;
  bidirectional?: boolean;
}

export interface QueryRequest {
  project_id: string;
  entity_types?: string[];
  entity_name?: string;
  mission?: string;
  aoi?: string;
  event_type?: string;
  relationship?: RelationshipFilter;
  confidence_min?: number;
  confidence_max?: number;
  review_status?: string;
  tags?: string[];
  classification?: string;
  analyst?: string;
  spatial?: SpatialFilter;
  temporal?: TemporalFilter;
  sort_by?: string;
  sort_direction?: string;
  max_results?: number;
  page?: number;
  page_size?: number;
  enrich?: boolean;
}

export interface QueryResult {
  items: Record<string, unknown>[];
  total: number;
  page: number;
  page_size: number;
  execution_time_ms: number;
  cached?: boolean;
  query_hash?: string;
}

export interface SaveQueryRequest {
  project_id: string;
  name: string;
  description?: string;
  filters_json: string;
  sort_by?: string;
  sort_direction?: string;
  max_results?: number;
  tags_json?: string;
  created_by?: string;
}

export interface SavedQuery {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  filters_json: string;
  sort_by: string | null;
  sort_direction: string;
  max_results: number;
  favorite: boolean;
  pinned: boolean;
  tags_json: string | null;
  created_by: string | null;
  created_at: string | null;
  modified_at: string | null;
}

export interface UpdateQueryRequest {
  name?: string;
  description?: string;
  filters_json?: string;
  sort_by?: string;
  sort_direction?: string;
  max_results?: number;
  favorite?: boolean;
  pinned?: boolean;
  tags_json?: string;
}

export interface QueryHistoryEntry {
  id: string;
  project_id: string;
  saved_query_id: string | null;
  filters_json: string;
  result_count: number;
  execution_time_ms: number;
  status: string;
  error_message: string | null;
  executed_by: string | null;
  executed_at: string | null;
}

export interface ExportRequest {
  project_id: string;
  format: string;
  filters?: Record<string, unknown>;
  query_ids?: string[];
}

export interface ExportResult {
  format: string;
  filename: string;
  content: string;
  count: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
