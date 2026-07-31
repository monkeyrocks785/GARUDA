import { useAssetStats } from "../../hooks/useAssets";
import { useAssetStore } from "../../store/useAssetStore";

export default function AssetStats() {
  const { projectId } = useAssetStore();
  const { data: stats, isLoading, isError } = useAssetStats();

  if (!projectId) {
    return (
      <div className="text-xs text-slate-500 text-center py-2">
        No project selected
      </div>
    );
  }

  if (isLoading || !stats) {
    return (
      <div className="text-xs text-slate-500 text-center py-2">
        Loading stats...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-xs text-red-400 text-center py-2">
        Failed to load stats
      </div>
    );
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">Total Assets</span>
        <span className="text-white font-medium">{stats.total}</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">Total Size</span>
        <span className="text-white font-medium">{formatBytes(stats.total_size_bytes)}</span>
      </div>
      {Object.keys(stats.by_type ?? {}).length > 0 && (
        <div className="pt-2 border-t border-slate-700/50">
          <p className="text-xs text-slate-500 mb-1">By Type</p>
          {Object.entries(stats.by_type ?? {}).map(([type, count]) => (
            <div key={type} className="flex justify-between text-xs">
              <span className="text-slate-400">{type}</span>
              <span className="text-slate-300">{String(count)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
