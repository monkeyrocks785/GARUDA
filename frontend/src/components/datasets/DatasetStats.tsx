import { useDatasetStats } from "../../hooks/useDatasets";
import { useDatasetStore } from "../../store/useDatasetStore";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export default function DatasetStats() {
  const { projectId } = useDatasetStore();
  const { data: stats, isLoading, isError } = useDatasetStats();

  if (!projectId) {
    return null;
  }

  if (isLoading || !stats) {
    return (
      <div className="p-3 text-xs text-slate-500 text-center">
        Loading stats...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-3 text-xs text-red-400 text-center">
        Failed to load stats
      </div>
    );
  }

  const data = stats;

  return (
    <div className="p-3 bg-slate-800/50 rounded-lg text-sm">
      <div className="font-medium mb-2 text-slate-300">Dataset Statistics</div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-slate-500">Total:</span>{" "}
          <span className="font-medium text-slate-200">{data.total}</span>
        </div>
        <div>
          <span className="text-slate-500">Size:</span>{" "}
          <span className="font-medium text-slate-200">{formatBytes(data.total_size_bytes)}</span>
        </div>
      </div>
      {Object.keys(data.by_type ?? {}).length > 0 && (
        <div className="mt-2 text-xs">
          <div className="text-slate-500 mb-1">By Type:</div>
          {Object.entries(data.by_type ?? {}).map(([type, count]) => (
            <div key={type} className="flex justify-between">
              <span className="text-slate-400">{type}</span>
              <span className="font-medium text-slate-200">{count as number}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
