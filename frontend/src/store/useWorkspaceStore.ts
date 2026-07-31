import { create } from "zustand";
import type { PanelLayout } from "../types/workspace";
import { DEFAULT_PANEL_LAYOUT } from "../types/workspace";

// eslint-disable-next-line @typescript-eslint/no-namespace
declare namespace GeoJSON {
  interface Geometry {
    type: string;
    coordinates: number[] | number[][] | number[][][] | number[][][][];
  }
}

interface WorkspaceStore {
  projectId: string | null;
  setProjectId: (id: string | null) => void;

  // Map view
  zoom: number;
  setZoom: (zoom: number) => void;
  center: [number, number];
  setCenter: (center: [number, number]) => void;
  mapRotation: number;
  setMapRotation: (rotation: number) => void;

  // Basemap
  basemap: string;
  setBasemap: (basemap: string) => void;

  // Active tool
  activeTool: string;
  setActiveTool: (tool: string) => void;

  // Selection
  selectedLayerId: string | null;
  setSelectedLayerId: (id: string | null) => void;
  selectedObjectId: string | null;
  setSelectedObjectId: (id: string | null) => void;
  selectedObjectType: string | null;
  setSelectedObjectType: (type: string | null) => void;

  // Panel layout
  panelLayout: PanelLayout;
  setPanelLayout: (layout: PanelLayout) => void;
  togglePanel: (panelId: string) => void;
  setPanelWidth: (panelId: string, width: number) => void;

  // Drawing
  isDrawing: boolean;
  setIsDrawing: (drawing: boolean) => void;
  drawingGeometry: GeoJSON.Geometry | null;
  setDrawingGeometry: (geometry: GeoJSON.Geometry | null) => void;

  // Measurement
  measurementResult: string | null;
  setMeasurementResult: (result: string | null) => void;

  // Mouse position (for status bar)
  mousePosition: [number, number] | null;
  setMousePosition: (pos: [number, number] | null) => void;

  // Undo/Redo
  undoStack: unknown[];
  redoStack: unknown[];
  pushUndo: (action: unknown) => void;
  undo: () => unknown | null;
  redo: () => unknown | null;

  // Visible layers
  visibleLayerIds: Set<string>;
  setVisibleLayerIds: (ids: Set<string>) => void;
  toggleLayerVisibility: (id: string) => void;

  // Reset
  resetWorkspace: () => void;
}

const initialState = {
  projectId: null as string | null,
  zoom: 2,
  center: [20, 0] as [number, number],
  mapRotation: 0,
  basemap: "osm",
  activeTool: "pan",
  selectedLayerId: null as string | null,
  selectedObjectId: null as string | null,
  selectedObjectType: null as string | null,
  panelLayout: { ...DEFAULT_PANEL_LAYOUT } as PanelLayout,
  isDrawing: false,
  drawingGeometry: null as GeoJSON.Geometry | null,
  measurementResult: null as string | null,
  mousePosition: null as [number, number] | null,
  undoStack: [] as unknown[],
  redoStack: [] as unknown[],
  visibleLayerIds: new Set<string>(),
};

export const useWorkspaceStore = create<WorkspaceStore>((set, get) => ({
  ...initialState,

  setProjectId: (id) => set({ projectId: id }),

  setZoom: (zoom) => set({ zoom }),
  setCenter: (center) => set({ center }),
  setMapRotation: (rotation) => set({ mapRotation: rotation }),

  setBasemap: (basemap) => set({ basemap }),

  setActiveTool: (tool) => set({ activeTool: tool }),

  setSelectedLayerId: (id) => set({ selectedLayerId: id }),
  setSelectedObjectId: (id) => set({ selectedObjectId: id }),
  setSelectedObjectType: (type) => set({ selectedObjectType: type }),

  setPanelLayout: (layout) => set({ panelLayout: layout }),
  togglePanel: (panelId) =>
    set((state) => ({
      panelLayout: {
        ...state.panelLayout,
        [panelId]: {
          ...state.panelLayout[panelId],
          visible: !state.panelLayout[panelId]?.visible,
        },
      },
    })),
  setPanelWidth: (panelId, width) =>
    set((state) => ({
      panelLayout: {
        ...state.panelLayout,
        [panelId]: {
          ...state.panelLayout[panelId],
          width,
        },
      },
    })),

  setIsDrawing: (drawing) => set({ isDrawing: drawing }),
  setDrawingGeometry: (geometry) => set({ drawingGeometry: geometry }),

  setMeasurementResult: (result) => set({ measurementResult: result }),

  setMousePosition: (pos) => set({ mousePosition: pos }),

  pushUndo: (action) =>
    set((state) => ({
      undoStack: [...state.undoStack, action],
      redoStack: [],
    })),
  undo: () => {
    const { undoStack } = get();
    if (undoStack.length === 0) return null;
    const action = undoStack[undoStack.length - 1];
    set((state) => ({
      undoStack: state.undoStack.slice(0, -1),
      redoStack: [...state.redoStack, action],
    }));
    return action;
  },
  redo: () => {
    const { redoStack } = get();
    if (redoStack.length === 0) return null;
    const action = redoStack[redoStack.length - 1];
    set((state) => ({
      redoStack: state.redoStack.slice(0, -1),
      undoStack: [...state.undoStack, action],
    }));
    return action;
  },

  setVisibleLayerIds: (ids) => set({ visibleLayerIds: ids }),
  toggleLayerVisibility: (id) =>
    set((state) => {
      const next = new Set(state.visibleLayerIds);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { visibleLayerIds: next };
    }),

  resetWorkspace: () => set(initialState),
}));
