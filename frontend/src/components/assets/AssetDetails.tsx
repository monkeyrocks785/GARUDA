import { useAsset, useAssetHistory, useAssetRelated, useToggleFavorite, useTogglePin, useArchiveAsset, useRestoreAsset, useDeleteAsset } from "../../hooks/useAssets";
import { useAssetStore } from "../../store/useAssetStore";
import type { AssetHistory, AssetRelationship } from "../../types/asset";
import { useState } from "react";
import { parseTagArray } from "../../utils/json";
import { getErrorMessage } from "../../utils/errorMessage";
import { useToastStore } from "../../store/useToastStore";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";
import EmptyState from "../ui/EmptyState";
import ConfirmDialog from "../ui/ConfirmDialog";

export default function AssetDetails() {
  const { selectedAssetId } = useAssetStore();
  const { data: asset, isLoading, isError, error, refetch } = useAsset(selectedAssetId);
  const { data: history } = useAssetHistory(selectedAssetId);
  const { data: related } = useAssetRelated(selectedAssetId);
  const toggleFavorite = useToggleFavorite();
  const togglePin = useTogglePin();
  const archiveAsset = useArchiveAsset();
  const restoreAsset = useRestoreAsset();
  const deleteAsset = useDeleteAsset();
  const toast = useToastStore.getState();
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  if (!selectedAssetId) {
    return (
      <EmptyState
        compact
        title="No asset selected"
        description="Select an asset to view details"
      />
    );
  }

  if (isLoading) {
    return <LoadingState compact label="Loading asset..." />;
  }

  if (isError) {
    return (
      <ErrorState
        compact
        title="Failed to load asset"
        message={getErrorMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  if (!asset) {
    return (
      <EmptyState
        compact
        title="No asset selected"
        description="Select an asset to view details"
      />
    );
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short", day: "numeric", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  };

  return (
    <div className="p-4 space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-start justify-between mb-2">
          <h2 className="text-xl font-bold text-white">{asset.display_name || asset.name}</h2>
          <span className="px-2 py-1 text-xs rounded-full bg-primary-500/20 text-primary-400">
            {asset.asset_type}
          </span>
        </div>
        {asset.description && (
          <p className="text-sm text-slate-400">{asset.description}</p>
        )}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2">
        <button
          onClick={() =>
            toggleFavorite.mutate(asset.id, {
              onSuccess: () =>
                toast.success(
                  asset.is_favorite ? "Removed from favorites" : "Added to favorites"
                ),
              onError: (err) => toast.error(getErrorMessage(err)),
            })
          }
          className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
            asset.is_favorite
              ? "border-yellow-500 bg-yellow-500/10 text-yellow-400"
              : "border-slate-600 text-slate-400 hover:bg-slate-700/50"
          }`}
        >
          {asset.is_favorite ? "★ Favorite" : "☆ Favorite"}
        </button>
        <button
          onClick={() =>
            togglePin.mutate(asset.id, {
              onSuccess: () =>
                toast.success(asset.is_pinned ? "Unpinned asset" : "Pinned asset"),
              onError: (err) => toast.error(getErrorMessage(err)),
            })
          }
          className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
            asset.is_pinned
              ? "border-blue-500 bg-blue-500/10 text-blue-400"
              : "border-slate-600 text-slate-400 hover:bg-slate-700/50"
          }`}
        >
          📌 Pin
        </button>
        {asset.is_archived ? (
          <button
            onClick={() =>
              restoreAsset.mutate(asset.id, {
                onSuccess: () => toast.success("Asset restored"),
                onError: (err) => toast.error(getErrorMessage(err)),
              })
            }
            className="px-3 py-1.5 text-sm rounded-lg border border-slate-600 text-green-400 hover:bg-slate-700/50"
          >
            Restore
          </button>
        ) : (
          <button
            onClick={() =>
              archiveAsset.mutate(asset.id, {
                onSuccess: () => toast.success("Asset archived"),
                onError: (err) => toast.error(getErrorMessage(err)),
              })
            }
            className="px-3 py-1.5 text-sm rounded-lg border border-slate-600 text-slate-400 hover:bg-slate-700/50"
          >
            Archive
          </button>
        )}
        <button
          onClick={() => setConfirmDeleteOpen(true)}
          className="px-3 py-1.5 text-sm rounded-lg border border-slate-600 text-red-400 hover:bg-slate-700/50"
        >
          Delete
        </button>
      </div>
      <ConfirmDialog
        open={confirmDeleteOpen}
        title="Delete asset"
        message={`Delete "${asset.display_name || asset.name}"? This cannot be undone.`}
        confirmLabel="Delete"
        danger
        onCancel={() => setConfirmDeleteOpen(false)}
        onConfirm={() => {
          deleteAsset.mutate(asset.id, {
            onSuccess: () => {
              toast.success("Asset deleted");
              setConfirmDeleteOpen(false);
            },
            onError: (err) => {
              toast.error(getErrorMessage(err));
              setConfirmDeleteOpen(false);
            },
          });
        }}
      />

      {/* Properties */}
      <div className="bg-slate-800/50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3">Properties</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">File Name</span>
            <span className="text-white">{asset.name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Type</span>
            <span className="text-white">{asset.asset_type}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Extension</span>
            <span className="text-white">{asset.extension}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Category</span>
            <span className="text-white">{asset.category || "N/A"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Size</span>
            <span className="text-white">{formatBytes(asset.file_size)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Version</span>
            <span className="text-white">v{asset.version}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Status</span>
            <span className="text-white">{asset.status}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Created</span>
            <span className="text-white">{formatDate(asset.created_at)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Modified</span>
            <span className="text-white">{formatDate(asset.modified_at)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Checksum</span>
            <span className="text-white font-mono text-xs">{asset.checksum}</span>
          </div>
        </div>
      </div>

      {/* Tags */}
      <div className="bg-slate-800/50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3">Tags</h3>
        {asset.tags ? (
          <div className="flex flex-wrap gap-2">
            {parseTagArray(asset.tags).map((tag: string, i: number) => (
              <span
                key={i}
                className="px-2 py-1 text-xs bg-slate-700/50 text-slate-300 rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500">No tags</p>
        )}
      </div>

      {/* Related Assets */}
      {related && related.related && related.related.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Related Assets</h3>
          <div className="space-y-2">
            {related.related.map((rel: AssetRelationship) => (
              <div key={rel.relationship_id} className="flex items-center gap-2 text-sm">
                <span className="text-slate-400">{rel.relationship_type}:</span>
                <span className="text-white">{rel.asset.display_name || rel.asset.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History */}
      {history && history.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">History</h3>
          <div className="space-y-2">
            {history.map((h: AssetHistory) => (
              <div key={h.id} className="flex items-start gap-3 text-sm">
                <span className="text-xs text-slate-500 shrink-0">{formatDate(h.timestamp)}</span>
                <div>
                  <span className="text-white capitalize">{h.action}</span>
                  {h.details && <span className="text-slate-400"> - {h.details}</span>}
                  {h.performed_by && (
                    <span className="text-slate-500"> by {h.performed_by}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
