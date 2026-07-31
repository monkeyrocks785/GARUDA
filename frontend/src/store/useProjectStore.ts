import { create } from "zustand";
import type { Project } from "../types";

interface ProjectState {
  // Current project being viewed
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;

  // Recent projects (client-side cache)
  recentProjects: Project[];
  setRecentProjects: (projects: Project[]) => void;

  // Search and filter state
  searchQuery: string;
  setSearchQuery: (query: string) => void;

  statusFilter: string | null;
  setStatusFilter: (status: string | null) => void;

  sortBy: "name" | "created_at" | "updated_at" | "last_opened_at";
  setSortBy: (sort: "name" | "created_at" | "updated_at" | "last_opened_at") => void;

  sortOrder: "asc" | "desc";
  setSortOrder: (order: "asc" | "desc") => void;

  showArchived: boolean;
  setShowArchived: (show: boolean) => void;

  // UI state
  selectedProjectIds: string[];
  setSelectedProjectIds: (ids: string[]) => void;
  toggleProjectSelection: (id: string) => void;
  clearSelection: () => void;

  // View mode
  viewMode: "grid" | "list";
  setViewMode: (mode: "grid" | "list") => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  // Current project
  currentProject: null,
  setCurrentProject: (project) => set({ currentProject: project }),

  // Recent projects
  recentProjects: [],
  setRecentProjects: (projects) => set({ recentProjects: projects }),

  // Search and filter
  searchQuery: "",
  setSearchQuery: (query) => set({ searchQuery: query }),

  statusFilter: null,
  setStatusFilter: (status) => set({ statusFilter: status }),

  sortBy: "updated_at",
  setSortBy: (sort) => set({ sortBy: sort }),

  sortOrder: "desc",
  setSortOrder: (order) => set({ sortOrder: order }),

  showArchived: false,
  setShowArchived: (show) => set({ showArchived: show }),

  // UI state
  selectedProjectIds: [],
  setSelectedProjectIds: (ids) => set({ selectedProjectIds: ids }),
  toggleProjectSelection: (id) =>
    set((state) => ({
      selectedProjectIds: state.selectedProjectIds.includes(id)
        ? state.selectedProjectIds.filter((i) => i !== id)
        : [...state.selectedProjectIds, id],
    })),
  clearSelection: () => set({ selectedProjectIds: [] }),

  // View mode
  viewMode: "grid",
  setViewMode: (mode) => set({ viewMode: mode }),
}));
