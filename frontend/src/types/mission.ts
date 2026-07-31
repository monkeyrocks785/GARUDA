export interface Mission {
  id: string;
  name: string;
  code?: string;
  description?: string;
  classification?: string;
  status: MissionStatus;
  priority: MissionPriority;
  created_by?: string;
  mission_start?: string;
  mission_end?: string;
  area_of_interest?: string;
  tags?: string;
  notes?: string;
  favorite: boolean;
  archived: boolean;
  project_count: number;
  dataset_count: number;
  pipeline_count: number;
  report_count: number;
  storage_path?: string;
  created_at: string;
  modified_at: string;
}

export type MissionStatus =
  | "support"
  | "planning"
  | "active"
  | "paused"
  | "completed"
  | "archived"
  | "cancelled";

export type MissionPriority = "low" | "medium" | "high" | "critical";

export interface MissionActivity {
  id: string;
  mission_id: string;
  action: string;
  details?: string;
  entity_type?: string;
  entity_id?: string;
  performed_by?: string;
  timestamp: string;
}

export interface MissionNote {
  id: string;
  mission_id: string;
  title?: string;
  content?: string;
  author?: string;
  created_at: string;
  modified_at: string;
}

export interface MissionProjectLink {
  mission_id: string;
  project_id: string;
  added_at: string;
  notes?: string;
}

export interface MissionStats {
  total: number;
  planning: number;
  active: number;
  completed: number;
  paused: number;
  archived: number;
  cancelled: number;
  total_projects: number;
}

export const STATUS_COLORS: Record<MissionStatus, string> = {
  support: "bg-blue-500/20 text-blue-400",
  planning: "bg-yellow-500/20 text-yellow-400",
  active: "bg-green-500/20 text-green-400",
  paused: "bg-orange-500/20 text-orange-400",
  completed: "bg-emerald-500/20 text-emerald-400",
  archived: "bg-slate-500/20 text-slate-400",
  cancelled: "bg-red-500/20 text-red-400",
};

export const PRIORITY_COLORS: Record<MissionPriority, string> = {
  low: "bg-slate-500/20 text-slate-400",
  medium: "bg-blue-500/20 text-blue-400",
  high: "bg-orange-500/20 text-orange-400",
  critical: "bg-red-500/20 text-red-400",
};
