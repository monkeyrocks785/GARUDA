import type { RasterMetadata } from "../../types/raster";

interface RasterPropertiesProps {
  raster: RasterMetadata;
  onClose: () => void;
}

export function RasterProperties({ raster, onClose }: RasterPropertiesProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="h-full flex flex-col bg-gray-800 text-white">
      <div className="flex items-center justify-between p-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200">Raster Properties</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white"
        >
          ×
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4 text-xs">
        <div>
          <h4 className="text-gray-400 mb-1">File</h4>
          <p className="text-gray-200 break-all">{raster.file_path}</p>
          <p className="text-gray-400 mt-1">
            {raster.file_format} • {formatFileSize(raster.file_size)}
          </p>
        </div>

        <div>
          <h4 className="text-gray-400 mb-1">Dimensions</h4>
          <p className="text-gray-200">
            {raster.width} × {raster.height} pixels
          </p>
          <p className="text-gray-400 mt-1">
            {raster.band_count} band{raster.band_count > 1 ? "s" : ""} • {raster.data_type}
          </p>
        </div>

        <div>
          <h4 className="text-gray-400 mb-1">CRS</h4>
          <p className="text-gray-200">{raster.crs}</p>
        </div>

        <div>
          <h4 className="text-gray-400 mb-1">Resolution</h4>
          <p className="text-gray-200">
            X: {raster.resolution_x.toFixed(6)}°
          </p>
          <p className="text-gray-200">
            Y: {raster.resolution_y.toFixed(6)}°
          </p>
        </div>

        <div>
          <h4 className="text-gray-400 mb-1">Bounds</h4>
          <p className="text-gray-200">
            Min: ({raster.bounds_min_x.toFixed(4)}, {raster.bounds_min_y.toFixed(4)})
          </p>
          <p className="text-gray-200">
            Max: ({raster.bounds_max_x.toFixed(4)}, {raster.bounds_max_y.toFixed(4)})
          </p>
        </div>

        {raster.nodata_value !== null && (
          <div>
            <h4 className="text-gray-400 mb-1">NoData</h4>
            <p className="text-gray-200">{raster.nodata_value}</p>
          </div>
        )}

        {raster.compression && (
          <div>
            <h4 className="text-gray-400 mb-1">Compression</h4>
            <p className="text-gray-200">{raster.compression}</p>
          </div>
        )}

        <div>
          <h4 className="text-gray-400 mb-1">Overviews</h4>
          <p className="text-gray-200">
            {raster.has_overviews ? "Built" : "Not built"}
          </p>
        </div>

        <div>
          <h4 className="text-gray-400 mb-1">Created</h4>
          <p className="text-gray-200">
            {new Date(raster.created_at).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
