import { useDatasetStore } from "../../store/useDatasetStore";
import { useDatasetStats } from "../../hooks/useDatasets";
import { DATASET_TYPES } from "../../types/dataset";

export default function DatasetFilter() {
  const {
    searchQuery,
    setSearchQuery,
    filterType,
    setFilterType,
    showFavoritesOnly,
    setShowFavoritesOnly,
    resetFilters,
  } = useDatasetStore();

  const { data: stats } = useDatasetStats();

  return (
    <div className="space-y-3 p-3 border-b">
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search datasets..."
        className="w-full px-3 py-2 border rounded text-sm"
      />

      <div className="flex flex-wrap gap-1">
        <button
          onClick={() => setFilterType(null)}
          className={`px-2 py-1 text-xs rounded ${
            !filterType ? "bg-blue-500 text-white" : "bg-gray-100 hover:bg-gray-200"
          }`}
        >
          All
          {stats && (
            <span className="ml-1">({stats.total})</span>
          )}
        </button>
        {DATASET_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => setFilterType(filterType === type ? null : type)}
            className={`px-2 py-1 text-xs rounded ${
              filterType === type
                ? "bg-blue-500 text-white"
                : "bg-gray-100 hover:bg-gray-200"
            }`}
          >
            {type}
            {stats?.by_type?.[type] && (
              <span className="ml-1">({stats.by_type[type]})</span>
            )}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-2">
        <label className="flex items-center gap-1 text-xs">
          <input
            type="checkbox"
            checked={showFavoritesOnly}
            onChange={(e) => setShowFavoritesOnly(e.target.checked)}
            className="rounded"
          />
          Favorites only
        </label>
        {(searchQuery || filterType || showFavoritesOnly) && (
          <button
            onClick={resetFilters}
            className="text-xs text-blue-500 hover:underline"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}
