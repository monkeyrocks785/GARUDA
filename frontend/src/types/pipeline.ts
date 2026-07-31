export interface Pipeline {
  id: string;
  project_id: string | null;
  name: string;
  description: string | null;
  version: number;
  status: string;
  progress: number;
  owner: string | null;
  priority: number;
  total_nodes: number;
  completed_nodes: number;
  failed_nodes: number;
  execution_time_ms: number;
  error_message: string | null;
  created_at: string;
  modified_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface PipelineNode {
  id: string;
  pipeline_id: string;
  name: string;
  description: string | null;
  node_type: string;
  status: string;
  inputs_json: string | null;
  outputs_json: string | null;
  parameters_json: string | null;
  depends_on_json: string | null;
  sort_order: number;
  retry_count: number;
  max_retries: number;
  execution_time_ms: number;
  error_message: string | null;
  result_json: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface PipelineHistory {
  id: string;
  pipeline_id: string;
  node_id: string | null;
  action: string;
  details: string | null;
  performed_by: string | null;
  execution_time_ms: number;
  timestamp: string;
}

export interface PipelineLog {
  id: string;
  pipeline_id: string;
  node_id: string | null;
  level: string;
  message: string;
  details: string | null;
  timestamp: string;
}

export interface QueueEntry {
  id: string;
  pipeline_id: string;
  status: string;
  priority: number;
  position: number;
  worker_id: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface QueueStatus {
  waiting: number;
  running: number;
  paused: number;
  completed: number;
  failed: number;
  cancelled: number;
  total: number;
}

export interface NodeType {
  type: string;
  name: string;
  description: string;
}

export interface PipelineStats {
  total: number;
  pending: number;
  queued: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
  paused: number;
}

export interface NodeConfig {
  name: string;
  description?: string;
  node_type: string;
  inputs?: Record<string, unknown>;
  parameters?: Record<string, unknown>;
  depends_on?: string[];
  max_retries?: number;
}

export const STATUS_COLORS: Record<string, string> = {
  pending: "bg-slate-500/20 text-slate-400",
  queued: "bg-blue-500/20 text-blue-400",
  running: "bg-blue-500/20 text-blue-400",
  paused: "bg-yellow-500/20 text-yellow-400",
  completed: "bg-green-500/20 text-green-400",
  failed: "bg-red-500/20 text-red-400",
  cancelled: "bg-slate-500/20 text-slate-400",
  skipped: "bg-slate-500/20 text-slate-400",
};

export const NODE_TYPE_ICONS: Record<string, string> = {
  import_file: "I",
  validate: "V",
  extract_metadata: "M",
  create_thumbnail: "T",
  save_db: "S",
  custom: "C",
};
