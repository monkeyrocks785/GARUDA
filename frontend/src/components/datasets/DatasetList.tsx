import { useState } from "react";
import { useDatasets, useDeleteDataset, useToggleFavorite } from "../../hooks/useDatasets";
import { useDatasetStore } from "../../store/useDatasetStore";
import type { Dataset } from "../../types/dataset";
import { parseTagArray } from "../../utils/json";
import { getErrorMessage } from "../../utils/errorMessage";
import { useToastStore } from "../../store/useToastStore";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";
import EmptyState from "../ui/EmptyState";

const TYPE_COLORS: Record<string, string> = {
  raster: "bg-blue-100 text-blue-800",
  vector: "bg-green-100 text-green-800",
  image: "bg-purple-100 text-purple-800",
  tabular: "bg-yellow-100 text-yellow-800",
  laser: "bg-red-100 text-red-800",
  other: "bg-gray-100 text-gray-800",
};

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export default function DatasetList() {
  const { data, isLoading, isError, error, refetch } = useDatasets();
  const deleteMutation = useDeleteDataset();
  const toggleFavMutation = useToggleFavorite();
  const { setSelectedDatasetId, selectedDatasetId } = useDatasetStore();
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const toast = useToastStore.getState();

  if (isLoading) {
    return <LoadingState compact label="Loading datasets..." />;
  }

  if (isError) {
    return (
      <ErrorState
        compact
        title="Failed to load datasets"
        message={getErrorMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  const datasets = data?.datasets || [];

  if (datasets.length === 0) {
    return (
      <EmptyState
        compact
        title="No datasets found"
        description="Import files to get started"
      />
    );
  }

  return (
    <div className="space-y-2">
      {datasets.map((dataset: Dataset) => (
        <div
          key={dataset.id}
          className={`p-3 border rounded-lg cursor-pointer transition-colors ${
            selectedDatasetId === dataset.id
              ? "border-blue-500 bg-blue-50"
              : "border-gray-200 hover:border-gray-300"
          }`}
          onClick={() => setSelectedDatasetId(dataset.id)}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-0.5 text-xs font-medium rounded ${
                    TYPE_COLORS[dataset.dataset_type] || "bg-gray-100 text-gray-800"
                  }`}
                >
                  {dataset.dataset_type.toUpperCase()}
                </span>
                <span className="text-xs text-gray-500">{dataset.extension}</span>
              </div>
              <div className="mt-1 font-medium text-sm truncate">{dataset.name}</div>
              <div className="text-xs text-gray-500 truncate">
                {dataset.original_filename}
              </div>
              <div className="flex items-center gap-4 mt-1 text-xs text-gray-400">
                <span>{formatBytes(dataset.file_size)}</span>
                <span>v{dataset.version}</span>
                {dataset.width && dataset.height && (
                  <span>
                    {dataset.width}x{dataset.height}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFavMutation.mutate(dataset.id, {
                    onSuccess: () =>
                      toast.success(
                        dataset.is_favorite
                          ? "Removed from favorites"
                          : "Added to favorites"
                      ),
                    onError: (err) => toast.error(getErrorMessage(err)),
                  });
                }}
                className={`p-1 rounded hover:bg-gray-100 ${
                  dataset.is_favorite ? "text-yellow-500" : "text-gray-400"
                }`}
              >
                {dataset.is_favorite ? "★" : "☆"}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirmDelete === dataset.id) {
                    deleteMutation.mutate(dataset.id, {
                      onSuccess: () => {
                        toast.success("Dataset deleted");
                        if (selectedDatasetId === dataset.id) {
                          setSelectedDatasetId(null);
                        }
                      },
                      onError: (err) => toast.error(getErrorMessage(err)),
                    });
                    setConfirmDelete(null);
                  } else {
                    setConfirmDelete(dataset.id);
                  }
                }}
                className={`p-1 rounded hover:bg-gray-100 ${
                  confirmDelete === dataset.id ? "text-red-500" : "text-gray-400"
                }`}
              >
                {confirmDelete === dataset.id ? "Confirm?" : "×"}
              </button>
            </div>
          </div>
          {dataset.tags && (
            <div className="flex gap-1 mt-2 flex-wrap">
              {parseTagArray(dataset.tags).map((tag: string) => (
                <span
                  key={tag}
                  className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
