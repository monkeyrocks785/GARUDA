import { create } from "zustand";
import type { AssetStats } from "../types/asset";

interface AssetStore {
  projectId: string | null;
  selectedAssetId: string | null;
  selectedCollectionId: string | null;
  searchQuery: string;
  filterType: string | null;
  filterCategory: string | null;
  filterTags: string[];
  showFavoritesOnly: boolean;
  showArchived: boolean;
  viewMode: "grid" | "list";
  sortBy: string;
  sortOrder: string;
  stats: AssetStats | null;

  setProjectId: (id: string | null) => void;
  setSelectedAssetId: (id: string | null) => void;
  setSelectedCollectionId: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  setFilterType: (type: string | null) => void;
  setFilterCategory: (category: string | null) => void;
  setFilterTags: (tags: string[]) => void;
  setShowFavoritesOnly: (show: boolean) => void;
  setShowArchived: (show: boolean) => void;
  setViewMode: (mode: "grid" | "list") => void;
  setSortBy: (field: string) => void;
  setSortOrder: (order: string) => void;
  setStats: (stats: AssetStats | null) => void;
  resetFilters: () => void;
}

export const useAssetStore = create<AssetStore>((set) => ({
  projectId: null,
  selectedAssetId: null,
  selectedCollectionId: null,
  searchQuery: "",
  filterType: null,
  filterCategory: null,
  filterTags: [],
  showFavoritesOnly: false,
  showArchived: false,
  viewMode: "grid",
  sortBy: "created_at",
  sortOrder: "desc",
  stats: null,

  setProjectId: (id) => set({ projectId: id }),
  setSelectedAssetId: (id) => set({ selectedAssetId: id }),
  setSelectedCollectionId: (id) => set({ selectedCollectionId: id }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setFilterType: (type) => set({ filterType: type }),
  setFilterCategory: (category) => set({ filterCategory: category }),
  setFilterTags: (tags) => set({ filterTags: tags }),
  setShowFavoritesOnly: (show) => set({ showFavoritesOnly: show }),
  setShowArchived: (show) => set({ showArchived: show }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setSortBy: (field) => set({ sortBy: field }),
  setSortOrder: (order) => set({ sortOrder: order }),
  setStats: (stats) => set({ stats: stats }),
  resetFilters: () =>
    set({
      searchQuery: "",
      filterType: null,
      filterCategory: null,
      filterTags: [],
      showFavoritesOnly: false,
      showArchived: false,
    }),
}));
