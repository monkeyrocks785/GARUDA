import { useAssetStore } from "../../store/useAssetStore";

const types = [
  "raster", "vector", "terrain", "document", "spreadsheet",
  "video", "audio", "image", "report", "model",
  "configuration", "log", "pipeline_result", "temporary", "other",
];

const categories = [
  "satellite", "drone", "survey", "analysis", "report",
  "model", "configuration", "data", "output", "archive", "system",
];

export default function AssetFilter() {
  const {
    filterType, filterCategory, showFavoritesOnly,
    showArchived, setFilterType, setFilterCategory,
    setShowFavoritesOnly, setShowArchived, resetFilters,
  } = useAssetStore();

  return (
    <div className="p-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase">Filters</span>
        <button
          onClick={resetFilters}
          className="text-xs text-primary-400 hover:text-primary-300"
        >
          Clear
        </button>
      </div>

      <div>
        <label className="text-xs text-slate-500 block mb-1">Type</label>
        <select
          value={filterType || ""}
          onChange={(e) => setFilterType(e.target.value || null)}
          className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
        >
          <option value="">All Types</option>
          {types.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="text-xs text-slate-500 block mb-1">Category</label>
        <select
          value={filterCategory || ""}
          onChange={(e) => setFilterCategory(e.target.value || null)}
          className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div className="space-y-1">
        <label className="text-xs text-slate-500 block mb-1">Quick Filters</label>
        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={showFavoritesOnly}
            onChange={(e) => setShowFavoritesOnly(e.target.checked)}
            className="rounded border-slate-500 bg-slate-700 text-primary-500"
          />
          Favorites only
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
            className="rounded border-slate-500 bg-slate-700 text-primary-500"
          />
          Show archived
        </label>
      </div>
    </div>
  );
}
