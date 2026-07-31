import { useAssets } from "../../hooks/useAssets";
import { useAssetStore } from "../../store/useAssetStore";
import type { Asset } from "../../types/asset";
import { getErrorMessage } from "../../utils/errorMessage";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";
import EmptyState from "../ui/EmptyState";

const TYPE_ICONS: Record<string, string> = {
  raster: "R", vector: "V", terrain: "T", document: "D",
  spreadsheet: "S", video: "VD", audio: "A", image: "I",
  report: "RP", model: "M", configuration: "C", log: "L",
  pipeline_result: "P", temporary: "TMP", other: "O",
};

export default function AssetList() {
  const { data, isLoading, isError, error, refetch } = useAssets();
  const { selectedAssetId, setSelectedAssetId, viewMode } = useAssetStore();

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  };

  if (isLoading) {
    return <LoadingState compact label="Loading assets..." />;
  }

  if (isError) {
    return (
      <ErrorState
        compact
        title="Failed to load assets"
        message={getErrorMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  const assets = data?.assets || [];

  if (assets.length === 0) {
    return (
      <EmptyState
        compact
        title="No assets found"
        description="Import files to get started"
      />
    );
  }

  if (viewMode === "grid") {
    return (
      <div className="p-3 grid grid-cols-2 gap-2">
        {assets.map((asset: Asset) => (
          <button
            key={asset.id}
            onClick={() => setSelectedAssetId(asset.id)}
            className={`text-left p-3 rounded-lg border transition-colors ${
              selectedAssetId === asset.id
                ? "border-primary-500 bg-primary-500/10"
                : "border-slate-700/50 bg-slate-800/30 hover:bg-slate-700/50"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="w-6 h-6 rounded bg-primary-600 flex items-center justify-center text-[10px] font-bold text-white">
                {TYPE_ICONS[asset.asset_type] || "?"}
              </span>
              <span className="text-xs text-slate-400 truncate">{asset.extension}</span>
              {asset.is_pinned && <span className="text-xs">📌</span>}
              {asset.is_favorite && <span className="text-xs">⭐</span>}
            </div>
            <p className="text-sm text-white truncate">{asset.display_name || asset.name}</p>
            <p className="text-xs text-slate-500">{formatBytes(asset.file_size)}</p>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="divide-y divide-slate-700/50">
      {assets.map((asset: Asset) => (
        <button
          key={asset.id}
          onClick={() => setSelectedAssetId(asset.id)}
          className={`w-full text-left px-4 py-3 flex items-center gap-3 transition-colors ${
            selectedAssetId === asset.id
              ? "bg-primary-500/10 border-l-2 border-primary-500"
              : "hover:bg-slate-700/30 border-l-2 border-transparent"
          }`}
        >
          <span className="w-8 h-8 rounded bg-primary-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
            {TYPE_ICONS[asset.asset_type] || "?"}
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-white truncate">{asset.display_name || asset.name}</p>
            <p className="text-xs text-slate-500">{asset.asset_type} · {formatBytes(asset.file_size)}</p>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {asset.is_pinned && <span className="text-xs">📌</span>}
            {asset.is_favorite && <span className="text-xs">⭐</span>}
            <span className="text-xs text-slate-500">{formatDate(asset.created_at)}</span>
          </div>
        </button>
      ))}
    </div>
  );
}
