export interface Timeline {
  id: string;
  project_id: string | null;
  name: string;
  description: string | null;
  group_by: string;
  sort_order: string;
  entry_count: number;
  favorite: boolean;
  archived: boolean;
  tags: string | null;
  notes: string | null;
  storage_path: string | null;
  created_at: string;
  modified_at: string;
}

export interface TimelineEntry {
  id: string;
  timeline_id: string;
  dataset_id: string;
  acquisition_date: string | null;
  acquisition_time: string | null;
  sensor_name: string | null;
  source: string | null;
  resolution: string | null;
  mission_id: string | null;
  aoi_id: string | null;
  dataset_type: string | null;
  sort_order: number;
  visibility: boolean;
  opacity: number;
  notes: string | null;
  created_at: string;
}

export interface ComparisonSession {
  id: string;
  timeline_id: string;
  name: string | null;
  mode: "side_by_side" | "swipe" | "single";
  left_entry_id: string | null;
  right_entry_id: string | null;
  swipe_position: number;
  opacity: number;
  linked_pan_zoom: boolean;
  map_center_lat: number | null;
  map_center_lng: number | null;
  map_zoom: number | null;
  status: string;
  created_at: string;
  modified_at: string;
}

export interface TimelineBookmark {
  id: string;
  timeline_id: string;
  entry_id: string | null;
  label: string;
  bookmark_date: string | null;
  color: string | null;
  notes: string | null;
  created_at: string;
}

export interface TimelineLog {
  id: string;
  timeline_id: string;
  action: string;
  details: string | null;
  entity_type: string | null;
  entity_id: string | null;
  timestamp: string;
}

export interface TimelineStats {
  total_timelines: number;
  total_entries: number;
}

export type ComparisonMode = "side_by_side" | "swipe" | "single";
export type GroupBy = "date" | "sensor" | "mission" | "project" | "type";

export const GROUP_BY_OPTIONS: { value: GroupBy; label: string }[] = [
  { value: "date", label: "Date" },
  { value: "sensor", label: "Sensor" },
  { value: "mission", label: "Mission" },
  { value: "project", label: "Project" },
  { value: "type", label: "Type" },
];

export const COMPARISON_MODE_COLORS: Record<ComparisonMode, string> = {
  side_by_side: "bg-blue-500/20 text-blue-400",
  swipe: "bg-green-500/20 text-green-400",
  single: "bg-slate-500/20 text-slate-400",
};
