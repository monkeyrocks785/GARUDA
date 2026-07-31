import { create } from "zustand";

interface PipelineStore {
  projectId: string | null;
  selectedPipelineId: string | null;
  view: "list" | "detail" | "queue" | "history";
  setProjectId: (id: string | null) => void;
  setSelectedPipelineId: (id: string | null) => void;
  setView: (view: "list" | "detail" | "queue" | "history") => void;
}

export const usePipelineStore = create<PipelineStore>((set) => ({
  projectId: null,
  selectedPipelineId: null,
  view: "list",

  setProjectId: (id) => set({ projectId: id }),
  setSelectedPipelineId: (id) => set({ selectedPipelineId: id }),
  setView: (view) => set({ view }),
}));
