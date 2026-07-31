import {
  useDataset,
  useDatasetVersions,
  useDatasetMetadata,
} from "../../hooks/useDatasets";
import { useDatasetStore } from "../../store/useDatasetStore";
import { getErrorMessage } from "../../utils/errorMessage";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";
import EmptyState from "../ui/EmptyState";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export default function DatasetDetails() {
  const { selectedDatasetId } = useDatasetStore();
  const { data: dataset, isLoading, isError, error, refetch } = useDataset(selectedDatasetId);
  const { data: versions } = useDatasetVersions(selectedDatasetId);
  const { data: metadata } = useDatasetMetadata(selectedDatasetId);

  if (!selectedDatasetId) {
    return (
      <EmptyState
        compact
        title="No dataset selected"
        description="Select a dataset to view details"
      />
    );
  }

  if (isLoading) {
    return <LoadingState compact label="Loading dataset..." />;
  }

  if (isError) {
    return (
      <ErrorState
        compact
        title="Failed to load dataset"
        message={getErrorMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  if (!dataset) {
    return (
      <EmptyState
        compact
        title="No dataset selected"
        description="Select a dataset to view details"
      />
    );
  }

  const data = dataset;

  return (
    <div className="space-y-4 p-4">
      <div>
        <h3 className="font-semibold text-lg">{data.name}</h3>
        <p className="text-sm text-gray-500">{data.original_filename}</p>
      </div>

      {data.description && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Description</div>
          <div className="text-sm">{data.description}</div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-xs font-medium text-gray-500">Type</div>
          <div className="text-sm">{data.dataset_type}</div>
        </div>
        <div>
          <div className="text-xs font-medium text-gray-500">Size</div>
          <div className="text-sm">{formatBytes(data.file_size)}</div>
        </div>
        <div>
          <div className="text-xs font-medium text-gray-500">Version</div>
          <div className="text-sm">v{data.version}</div>
        </div>
        <div>
          <div className="text-xs font-medium text-gray-500">Status</div>
          <div className="text-sm">{data.status}</div>
        </div>
        {data.coordinate_system && (
          <div>
            <div className="text-xs font-medium text-gray-500">CRS</div>
            <div className="text-sm">{data.coordinate_system}</div>
          </div>
        )}
        {data.width && data.height && (
          <div>
            <div className="text-xs font-medium text-gray-500">Dimensions</div>
            <div className="text-sm">
              {data.width} x {data.height}
            </div>
          </div>
        )}
        {data.bands && (
          <div>
            <div className="text-xs font-medium text-gray-500">Bands</div>
            <div className="text-sm">{data.bands}</div>
          </div>
        )}
      </div>

      {data.bbox_min_x !== null && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Bounding Box</div>
          <div className="text-xs font-mono bg-gray-50 p-2 rounded">
            <div>
              Min: {data.bbox_min_x?.toFixed(6)}, {data.bbox_min_y?.toFixed(6)}
            </div>
            <div>
              Max: {data.bbox_max_x?.toFixed(6)}, {data.bbox_max_y?.toFixed(6)}
            </div>
          </div>
        </div>
      )}

      {versions && versions.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Version History</div>
          <div className="space-y-1">
            {versions.map((v) => (
              <div
                key={v.id}
                className="text-xs p-2 bg-gray-50 rounded flex justify-between"
              >
                <span>v{v.version_number}</span>
                <span className="text-gray-500">{v.change_description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {metadata && Object.keys(metadata).length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Metadata</div>
          <div className="text-xs font-mono bg-gray-50 p-2 rounded max-h-48 overflow-auto">
            {Object.entries(metadata).map(([key, val]) => (
              <div key={key}>
                <span className="text-gray-500">{key}:</span> {val.value}
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <div className="text-xs font-medium text-gray-500 mb-1">Checksum (SHA256)</div>
        <div className="text-xs font-mono bg-gray-50 p-2 rounded break-all">
          {data.checksum}
        </div>
      </div>
    </div>
  );
}
