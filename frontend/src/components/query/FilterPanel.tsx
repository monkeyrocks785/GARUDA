import type { QueryConfig, QueryRequest, SavedQuery } from "../../types/query";

interface FilterPanelProps {
  config: QueryConfig | null;
  query: QueryRequest;
  onChange: (query: QueryRequest) => void;
  onRun: () => void;
  running: boolean;
  savedQueries: SavedQuery[];
  savedQueryId: string | null;
}

const ENTITY_COLORS: Record<string, string> = {
  road: "bg-amber-100 text-amber-800 border-amber-300",
  bridge: "bg-cyan-100 text-cyan-800 border-cyan-300",
  building: "bg-violet-100 text-violet-800 border-violet-300",
  settlement: "bg-pink-100 text-pink-800 border-pink-300",
  river: "bg-blue-100 text-blue-800 border-blue-300",
  vegetation: "bg-green-100 text-green-800 border-green-300",
  airfield: "bg-orange-100 text-orange-800 border-orange-300",
  tunnel: "bg-stone-100 text-stone-800 border-stone-300",
  railway: "bg-red-100 text-red-800 border-red-300",
  port: "bg-teal-100 text-teal-800 border-teal-300",
  unknown: "bg-gray-100 text-gray-800 border-gray-300",
};

export default function FilterPanel({
  config,
  query,
  onChange,
  savedQueries,
}: FilterPanelProps) {
  const toggleEntityType = (type: string) => {
    const current = query.entity_types || [];
    const next = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type];
    onChange({ ...query, entity_types: next.length > 0 ? next : undefined });
  };

  const setFilter = (key: keyof QueryRequest, value: unknown) => {
    onChange({ ...query, [key]: value });
  };

  return (
    <div className="w-80 border-r bg-gray-50 overflow-y-auto flex-shrink-0">
      <div className="p-4">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
          Filters
        </h2>

        {/* Entity Types */}
        <div className="mb-5">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Entity Types</h3>
          <div className="flex flex-wrap gap-1.5">
            {(config?.entity_types || []).map((type) => {
              const active = query.entity_types?.includes(type);
              return (
                <button
                  key={type}
                  onClick={() => toggleEntityType(type)}
                  className={`px-2.5 py-1 text-xs rounded-full border font-medium transition-colors ${
                    active
                      ? ENTITY_COLORS[type] || "bg-blue-100 text-blue-800 border-blue-300"
                      : "bg-white text-gray-500 border-gray-200 hover:border-gray-300"
                  }`}
                >
                  {type}
                </button>
              );
            })}
          </div>
        </div>

        {/* Entity Name */}
        <div className="mb-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Entity Name</h3>
          <input
            value={query.entity_name || ""}
            onChange={(e) => setFilter("entity_name", e.target.value || undefined)}
            placeholder="Search by name..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>

        {/* Confidence */}
        <div className="mb-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Confidence</h3>
          <div className="flex gap-2">
            <input
              type="number"
              min={0}
              max={1}
              step={0.1}
              value={query.confidence_min ?? ""}
              onChange={(e) => setFilter("confidence_min", e.target.value ? Number(e.target.value) : undefined)}
              placeholder="Min"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
            <input
              type="number"
              min={0}
              max={1}
              step={0.1}
              value={query.confidence_max ?? ""}
              onChange={(e) => setFilter("confidence_max", e.target.value ? Number(e.target.value) : undefined)}
              placeholder="Max"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
        </div>

        {/* Review Status */}
        <div className="mb-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Review Status</h3>
          <select
            value={query.review_status || ""}
            onChange={(e) => setFilter("review_status", e.target.value || undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          >
            <option value="">Any</option>
            {(config?.review_statuses || []).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {/* Tags */}
        <div className="mb-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Tags</h3>
          <input
            value={(query.tags || []).join(", ")}
            onChange={(e) => setFilter("tags", e.target.value ? e.target.value.split(",").map((t) => t.trim()) : undefined)}
            placeholder="Comma-separated tags"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>

        {/* Spatial */}
        <div className="mb-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Spatial</h3>
          <div className="space-y-2">
            <select
              value={query.spatial?.operator || ""}
              onChange={(e) => {
                if (e.target.value) {
                  onChange({ ...query, spatial: { operator: e.target.value } });
                } else {
                  const { spatial: _, ...rest } = query;
                  onChange(rest);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
            >
              <option value="">None</option>
              {(config?.spatial_operators || []).map((op) => (
                <option key={op} value={op}>{op}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Temporal */}
        <div className="mb-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Temporal</h3>
          <select
            value={query.temporal?.operator || ""}
            onChange={(e) => {
              if (e.target.value) {
                onChange({ ...query, temporal: { operator: e.target.value } });
              } else {
                const { temporal: _, ...rest } = query;
                onChange(rest);
              }
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          >
            <option value="">None</option>
            {(config?.temporal_operators || []).map((op) => (
              <option key={op} value={op}>{op}</option>
            ))}
          </select>
          {query.temporal && (
            <div className="mt-2 space-y-2">
              {["before", "after"].includes(query.temporal.operator) && (
                <input
                  type="datetime-local"
                  value={query.temporal.date?.slice(0, 16) || ""}
                  onChange={(e) => setFilter("temporal", { ...query.temporal!, date: e.target.value ? new Date(e.target.value).toISOString() : undefined })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              )}
              {query.temporal.operator === "between" && (
                <div className="flex gap-2">
                  <input
                    type="datetime-local"
                    value={query.temporal.date_from?.slice(0, 16) || ""}
                    onChange={(e) => setFilter("temporal", { ...query.temporal!, date_from: e.target.value ? new Date(e.target.value).toISOString() : undefined })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                  <input
                    type="datetime-local"
                    value={query.temporal.date_to?.slice(0, 16) || ""}
                    onChange={(e) => setFilter("temporal", { ...query.temporal!, date_to: e.target.value ? new Date(e.target.value).toISOString() : undefined })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Event Type */}
        <div className="mb-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Event Type</h3>
          <select
            value={query.event_type || ""}
            onChange={(e) => setFilter("event_type", e.target.value || undefined)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          >
            <option value="">Any</option>
            {(config?.event_types || []).map((et) => (
              <option key={et} value={et}>{et}</option>
            ))}
          </select>
        </div>

        {/* Saved Queries */}
        {savedQueries.length > 0 && (
          <div className="mb-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Saved Queries</h3>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {savedQueries.filter((sq) => sq.pinned).map((sq) => (
                <button
                  key={sq.id}
                  onClick={() => {
                    try {
                      const filters = JSON.parse(sq.filters_json);
                      onChange({ ...query, ...filters });
                    } catch {
                      // ignore
                    }
                  }}
                  className="w-full text-left px-3 py-1.5 text-xs bg-white border border-gray-200 rounded-lg hover:bg-gray-100 truncate"
                >
                  {sq.favorite ? "★ " : ""}{sq.name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
