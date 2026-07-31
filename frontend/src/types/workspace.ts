export interface WorkspaceState {
  id: string;
  project_id: string;
  zoom: number;
  center_lat: number;
  center_lng: number;
  map_rotation: number;
  basemap: string;
  active_tool: string | null;
  selected_layer_id: string | null;
  selected_object_id: string | null;
  selected_object_type: string | null;
  visible_layers: string | null;
  panel_layout: string | null;
  drawing_features: string | null;
  measurement_features: string | null;
  undo_stack: string | null;
  redo_stack: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceStateUpdate {
  zoom?: number;
  center_lat?: number;
  center_lng?: number;
  map_rotation?: number;
  basemap?: string;
  active_tool?: string;
  selected_layer_id?: string;
  selected_object_id?: string;
  selected_object_type?: string;
  visible_layers?: string;
  panel_layout?: string;
  drawing_features?: string;
  measurement_features?: string;
  undo_stack?: string;
  redo_stack?: string;
}

export interface PanelLayout {
  [panelId: string]: {
    visible: boolean;
    width: number;
    height?: number;
    position: "left" | "right" | "bottom";
  };
}

export const DEFAULT_PANEL_LAYOUT: PanelLayout = {
  projectExplorer: { visible: true, width: 260, position: "left" },
  layerManager: { visible: true, width: 280, position: "left" },
  propertiesPanel: { visible: true, width: 300, position: "right" },
  timelineDock: { visible: false, width: 0, height: 200, position: "bottom" },
};

export const BASEMAPS = [
  { id: "blank_grid", name: "Blank Grid", url: "" },
] as const;

export type BasemapId = (typeof BASEMAPS)[number]["id"];

export const BASEMAP_URLS: Record<string, string> = {};
for (const b of BASEMAPS) {
  if (b.url) BASEMAP_URLS[b.id] = b.url;
}
