import { create } from "zustand";

interface MissionState {
  selectedMissionId: string | null;
  view: "list" | "dashboard" | "detail" | "timeline" | "notes";
  setSelectedMissionId: (id: string | null) => void;
  setView: (view: MissionState["view"]) => void;
}

export const useMissionStore = create<MissionState>((set) => ({
  selectedMissionId: null,
  view: "list",
  setSelectedMissionId: (id) => set({ selectedMissionId: id }),
  setView: (view) => set({ view }),
}));
