import { create } from "zustand";
import type { DatasetStats } from "../types/dataset";

interface DatasetStore {
  projectId: string | null;
  selectedDatasetId: string | null;
  searchQuery: string;
  filterType: string | null;
  filterExtension: string | null;
  filterTags: string[];
  showFavoritesOnly: boolean;
  sortBy: string;
  sortOrder: string;
  stats: DatasetStats | null;

  setProjectId: (id: string | null) => void;
  setSelectedDatasetId: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  setFilterType: (type: string | null) => void;
  setFilterExtension: (ext: string | null) => void;
  setFilterTags: (tags: string[]) => void;
  setShowFavoritesOnly: (show: boolean) => void;
  setSortBy: (field: string) => void;
  setSortOrder: (order: string) => void;
  setStats: (stats: DatasetStats | null) => void;
  resetFilters: () => void;
}

export const useDatasetStore = create<DatasetStore>((set) => ({
  projectId: null,
  selectedDatasetId: null,
  searchQuery: "",
  filterType: null,
  filterExtension: null,
  filterTags: [],
  showFavoritesOnly: false,
  sortBy: "created_at",
  sortOrder: "desc",
  stats: null,

  setProjectId: (id) => set({ projectId: id }),
  setSelectedDatasetId: (id) => set({ selectedDatasetId: id }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setFilterType: (type) => set({ filterType: type }),
  setFilterExtension: (ext) => set({ filterExtension: ext }),
  setFilterTags: (tags) => set({ filterTags: tags }),
  setShowFavoritesOnly: (show) => set({ showFavoritesOnly: show }),
  setSortBy: (field) => set({ sortBy: field }),
  setSortOrder: (order) => set({ sortOrder: order }),
  setStats: (stats) => set({ stats: stats }),
  resetFilters: () =>
    set({
      searchQuery: "",
      filterType: null,
      filterExtension: null,
      filterTags: [],
      showFavoritesOnly: false,
    }),
}));
