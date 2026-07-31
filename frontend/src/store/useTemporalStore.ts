import { create } from "zustand";

interface TemporalState {
  selectedTimelineId: string | null;
  selectedEntryId: string | null;
  view: "list" | "detail" | "comparison" | "playback";
  comparisonMode: "side_by_side" | "swipe" | "single";
  dateRange: { from: string | null; to: string | null };
  sensorFilter: string | null;
  setSelectedTimelineId: (id: string | null) => void;
  setSelectedEntryId: (id: string | null) => void;
  setView: (view: TemporalState["view"]) => void;
  setComparisonMode: (mode: TemporalState["comparisonMode"]) => void;
  setDateRange: (range: { from: string | null; to: string | null }) => void;
  setSensorFilter: (sensor: string | null) => void;
}

export const useTemporalStore = create<TemporalState>((set) => ({
  selectedTimelineId: null,
  selectedEntryId: null,
  view: "list",
  comparisonMode: "side_by_side",
  dateRange: { from: null, to: null },
  sensorFilter: null,
  setSelectedTimelineId: (id) => set({ selectedTimelineId: id }),
  setSelectedEntryId: (id) => set({ selectedEntryId: id }),
  setView: (view) => set({ view }),
  setComparisonMode: (mode) => set({ comparisonMode: mode }),
  setDateRange: (range) => set({ dateRange: range }),
  setSensorFilter: (sensor) => set({ sensorFilter: sensor }),
}));
