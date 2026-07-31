import { useRef, useState } from "react";
import { useImportDataset, useImportFolder } from "../../hooks/useDatasets";
import { useDatasetStore } from "../../store/useDatasetStore";
import { useToastStore } from "../../store/useToastStore";
import { getErrorMessage } from "../../utils/errorMessage";

export default function DatasetImport() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [folderPath, setFolderPath] = useState("");
  const [importMode, setImportMode] = useState<"file" | "folder">("file");
  const importFileMutation = useImportDataset();
  const importFolderMutation = useImportFolder();
  const { projectId } = useDatasetStore();
  const toast = useToastStore.getState();

  const handleFileImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    try {
      for (let i = 0; i < files.length; i++) {
        await importFileMutation.mutateAsync({ file: files[i] });
      }
      toast.success(files.length > 1 ? `${files.length} files imported` : "Dataset imported");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleFolderImport = async () => {
    if (!folderPath.trim()) return;
    try {
      await importFolderMutation.mutateAsync({ folderPath: folderPath.trim() });
      toast.success("Folder imported");
      setFolderPath("");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const isLoading = importFileMutation.isPending || importFolderMutation.isPending;

  return (
    <div className="p-4 border rounded-lg bg-white">
      <h3 className="font-semibold mb-3">Import Datasets</h3>

      <div className="flex gap-2 mb-3">
        <button
          onClick={() => setImportMode("file")}
          className={`px-3 py-1.5 text-sm rounded ${
            importMode === "file"
              ? "bg-blue-500 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          File(s)
        </button>
        <button
          onClick={() => setImportMode("folder")}
          className={`px-3 py-1.5 text-sm rounded ${
            importMode === "folder"
              ? "bg-blue-500 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          Folder
        </button>
      </div>

      {importMode === "file" ? (
        <div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileImport}
            accept=".tif,.tiff,.geotiff,.jp2,.png,.jpg,.jpeg,.dem,.shp,.geojson,.gpkg,.kml,.csv,.json,.xml,.las,.laz"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading || !projectId}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
          >
            {isLoading ? "Importing..." : "Select Files"}
          </button>
          <p className="text-xs text-gray-500 mt-1">
            Supports: GeoTIFF, JPEG2000, PNG, JPEG, Shapefile, GeoJSON, GeoPackage, KML, CSV
          </p>
        </div>
      ) : (
        <div>
          <div className="flex gap-2">
            <input
              type="text"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              placeholder="Enter folder path..."
              className="flex-1 px-3 py-2 border rounded text-sm"
            />
            <button
              onClick={handleFolderImport}
              disabled={isLoading || !folderPath.trim() || !projectId}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
            >
              {isLoading ? "Importing..." : "Import"}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Scans folder for all supported file types
          </p>
        </div>
      )}

      {!projectId && (
        <p className="text-xs text-red-500 mt-2">
          Select a project first to import datasets
        </p>
      )}
    </div>
  );
}
