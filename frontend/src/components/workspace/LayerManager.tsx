import { useState } from "react";
import {
  useLayers,
  useToggleLayerVisibility,
  useDeleteLayer,
  useUpdateLayer,
  useImportGeoJSON,
  useImportKML,
  useImportShapefile,
  useImportRaster,
  useRegisterAssetLayer,
  useProjectAssets,
} from "../../hooks/useGeospatial";
import { useAOIs, useDeleteAOI } from "../../hooks/useGeospatial";
import { useWorkspaceStore } from "../../store/useWorkspaceStore";
import { useToastStore } from "../../store/useToastStore";
import { getErrorMessage } from "../../utils/errorMessage";
import ErrorState from "../ui/ErrorState";

interface LayerManagerProps {
  projectId: string | undefined;
}

export default function LayerManager({ projectId }: LayerManagerProps) {
  const { selectedLayerId, setSelectedLayerId } = useWorkspaceStore();
  const [importMenuOpen, setImportMenuOpen] = useState(false);
  const [assetPickerOpen, setAssetPickerOpen] = useState(false);
  const [editingLayerId, setEditingLayerId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    layerId: string;
  } | null>(null);

  const { data: layers = [], isLoading: layersLoading, isError: layersError, error: layersErrorObj, refetch: refetchLayers } = useLayers(projectId || null);
  const { data: aois = [] } = useAOIs(projectId || null);
  const { data: assets = [], isLoading: assetsLoading } = useProjectAssets(projectId || null);
  const toast = useToastStore.getState();

  const toggleVisibility = useToggleLayerVisibility();
  const deleteLayer = useDeleteLayer();
  const updateLayer = useUpdateLayer();
  const deleteAOI = useDeleteAOI();

  const importGeoJSON = useImportGeoJSON();
  const importKML = useImportKML();
  const importShapefile = useImportShapefile();
  const importRaster = useImportRaster();
  const registerAssetLayer = useRegisterAssetLayer();

  const handleFileImport = async (type: "geojson" | "kml" | "shapefile" | "raster", file: File) => {
    if (!projectId) return;
    try {
      if (type === "geojson") await importGeoJSON.mutateAsync({ projectId, file });
      else if (type === "kml") await importKML.mutateAsync({ projectId, file });
      else if (type === "shapefile") await importShapefile.mutateAsync({ projectId, file });
      else if (type === "raster") await importRaster.mutateAsync({ projectId, file });
      toast.success(type === "raster" ? "Raster imported" : "Layer imported");
      setImportMenuOpen(false);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const handleFileInput = (type: "geojson" | "kml" | "shapefile" | "raster") => {
    const input = document.createElement("input");
    input.type = "file";
    if (type === "geojson") input.accept = ".geojson,.json";
    else if (type === "kml") input.accept = ".kml";
    else if (type === "shapefile") input.accept = ".zip";
    else if (type === "raster") input.accept = ".tif,.tiff";
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) handleFileImport(type, file);
    };
    input.click();
  };

  const handleRegisterAsset = async (assetId: string, assetName: string) => {
    if (!projectId) return;
    try {
      await registerAssetLayer.mutateAsync({ projectId, assetId, name: assetName });
      toast.success("Asset added as layer");
      setAssetPickerOpen(false);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const startRename = (layerId: string, currentName: string) => {
    setEditingLayerId(layerId);
    setEditName(currentName);
  };

  const commitRename = (layerId: string) => {
    if (projectId && editName.trim()) {
      updateLayer.mutate({ projectId, layerId, data: { name: editName.trim() } });
    }
    setEditingLayerId(null);
  };

  const handleContextMenu = (e: React.MouseEvent, layerId: string) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, layerId });
  };

  const sortedLayers = [...layers].sort((a, b) => b.z_index - a.z_index);

  const allVisible = sortedLayers.every((l) => l.visible !== false);
  const handleToggleAll = () => {
    if (!projectId) return;
    sortedLayers.forEach((layer) => {
      const shouldShow = allVisible ? false : true;
      const isVisible = layer.visible !== false;
      if (isVisible !== shouldShow) {
        toggleVisibility.mutate({ projectId, layerId: layer.id });
      }
    });
  };

  return (
    <div className="flex flex-col h-full relative">
      {/* Header */}
      <div className="p-3 border-b border-slate-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-white text-sm">Layers</h3>
          <div className="flex items-center gap-1">
            <button
              onClick={handleToggleAll}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              title="Toggle All Visibility"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
            <div className="relative">
              <button
                onClick={() => setImportMenuOpen(!importMenuOpen)}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                title="Import File"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
              {importMenuOpen && (
                <div className="absolute right-0 top-full mt-1 w-52 bg-slate-800 border border-slate-700 rounded-lg shadow-lg z-50">
                  <button onClick={() => handleFileInput("geojson")} className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700 rounded-t-lg">
                    Import GeoJSON
                  </button>
                  <button onClick={() => handleFileInput("kml")} className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700">
                    Import KML
                  </button>
                  <button onClick={() => handleFileInput("shapefile")} className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700">
                    Import Shapefile (ZIP)
                  </button>
                  <button onClick={() => handleFileInput("raster")} className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700">
                    Import Raster (GeoTIFF)
                  </button>
                  <button onClick={() => { setImportMenuOpen(false); setAssetPickerOpen(true); }} className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700 rounded-b-lg">
                    Register Asset as Layer
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Layer list */}
      <div className="flex-1 overflow-y-auto">
        {layersLoading ? (
          <div className="p-4 text-center text-slate-400 text-sm">Loading layers...</div>
        ) : layersError ? (
          <ErrorState
            compact
            title="Failed to load layers"
            message={getErrorMessage(layersErrorObj)}
            onRetry={() => refetchLayers()}
          />
        ) : sortedLayers.length === 0 ? (
          <div className="p-4 text-center text-slate-400 text-sm">
            No layers yet. Import a file or draw an AOI.
          </div>
        ) : (
          <div className="p-1 space-y-0.5">
            {sortedLayers.map((layer) => {
              const isVisible = layer.visible !== false;
              return (
                <div
                  key={layer.id}
                  className={`flex items-center gap-1.5 p-1.5 rounded cursor-pointer transition-colors group ${
                    selectedLayerId === layer.id
                      ? "bg-primary-600/20 border border-primary-500/50"
                      : "hover:bg-slate-700/50"
                  }`}
                  onClick={() => setSelectedLayerId(layer.id)}
                  onContextMenu={(e) => handleContextMenu(e, layer.id)}
                >
                  {/* Visibility */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (projectId) toggleVisibility.mutate({ projectId, layerId: layer.id });
                    }}
                    className={`p-0.5 rounded ${isVisible ? "text-white" : "text-slate-500"}`}
                  >
                    {isVisible ? (
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    )}
                  </button>

                  {/* Layer icon */}
                  <span className="text-xs">
                    {layer.layer_type === "raster" ? "🖼️" : layer.layer_type === "aoi" ? "🎯" : "📍"}
                  </span>

                  {/* Name */}
                  <div className="flex-1 min-w-0">
                    {editingLayerId === layer.id ? (
                      <input
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onBlur={() => commitRename(layer.id)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") commitRename(layer.id);
                          if (e.key === "Escape") setEditingLayerId(null);
                        }}
                        className="w-full bg-slate-900 border border-primary-500 rounded px-1 text-xs text-white"
                        autoFocus
                      />
                    ) : (
                      <p className="text-xs text-white truncate">{layer.name}</p>
                    )}
                  </div>

                  {/* Opacity indicator */}
                  <span className="text-[10px] text-slate-500">{Math.round(layer.opacity * 100)}%</span>

                  {/* Delete */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (projectId && confirm("Delete this layer?")) {
                        deleteLayer.mutate(
                          { projectId, layerId: layer.id },
                          {
                            onSuccess: () => toast.success("Layer deleted"),
                            onError: (err) => toast.error(getErrorMessage(err)),
                          }
                        );
                      }
                    }}
                    className="p-0.5 text-slate-400 hover:text-red-400 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* AOI Section */}
      {aois.length > 0 && (
        <div className="border-t border-slate-700">
          <div className="p-2">
            <h4 className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-1">
              Areas of Interest
            </h4>
            <div className="space-y-0.5">
              {aois.map((aoi) => (
                <div
                  key={aoi.id}
                  className="flex items-center gap-1.5 p-1.5 text-xs text-slate-300 hover:bg-slate-700/50 rounded cursor-pointer"
                  onClick={() => {
                    setSelectedLayerId(null);
                    useWorkspaceStore.getState().setSelectedObjectId(aoi.id);
                    useWorkspaceStore.getState().setSelectedObjectType("aoi");
                  }}
                >
                  <div className="w-2.5 h-2.5 rounded" style={{ backgroundColor: aoi.fill_color }} />
                  <span className="flex-1 truncate">{aoi.name}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (projectId && confirm("Delete this AOI?")) {
                        deleteAOI.mutate(
                          { projectId, aoiId: aoi.id },
                          {
                            onSuccess: () => toast.success("AOI deleted"),
                            onError: (err) => toast.error(getErrorMessage(err)),
                          }
                        );
                      }
                    }}
                    className="p-0.5 text-slate-400 hover:text-red-400 rounded opacity-0 group-hover:opacity-100"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Asset Picker */}
      {assetPickerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-xl w-full max-w-sm flex flex-col max-h-[70%]">
            <div className="p-3 border-b border-slate-700 flex items-center justify-between">
              <h4 className="text-sm font-medium text-white">Register Asset as Layer</h4>
              <button
                onClick={() => setAssetPickerOpen(false)}
                className="p-1 text-slate-400 hover:text-white rounded"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {assetsLoading ? (
                <div className="p-4 text-center text-slate-400 text-sm">Loading assets...</div>
              ) : assets.length === 0 ? (
                <div className="p-4 text-center text-slate-400 text-sm">
                  No assets in this project yet.
                </div>
              ) : (
                <div className="space-y-1">
                  {assets.map((asset) => (
                    <button
                      key={asset.id}
                      onClick={() => handleRegisterAsset(asset.id, asset.display_name || asset.name)}
                      className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700 rounded"
                    >
                      <span className="text-xs">📎</span>
                      <span className="flex-1 truncate">{asset.display_name || asset.name}</span>
                      <span className="text-[10px] text-slate-500 uppercase">{asset.asset_type}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="p-2 border-t border-slate-700">
              <p className="text-[10px] text-slate-500">
                Rasters and vector files (GeoJSON, KML, ZIP) can be displayed in the GIS workspace.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="fixed z-50 bg-slate-800 border border-slate-700 rounded-lg shadow-lg py-1 min-w-[140px]"
          style={{ left: contextMenu.x, top: contextMenu.y }}
          onMouseLeave={() => setContextMenu(null)}
        >
          <button
            onClick={() => {
              const layer = layers.find((l) => l.id === contextMenu.layerId);
              if (layer) startRename(layer.id, layer.name);
              setContextMenu(null);
            }}
            className="w-full px-3 py-1.5 text-left text-sm text-slate-300 hover:bg-slate-700"
          >
            Rename
          </button>
          <button
            onClick={() => {
              if (projectId) {
                const layer = layers.find((l) => l.id === contextMenu.layerId);
                if (layer) {
                  updateLayer.mutate({
                    projectId,
                    layerId: contextMenu.layerId,
                    data: { opacity: Math.max(0, layer.opacity - 0.1) },
                  });
                }
              }
              setContextMenu(null);
            }}
            className="w-full px-3 py-1.5 text-left text-sm text-slate-300 hover:bg-slate-700"
          >
            Decrease Opacity
          </button>
          <button
            onClick={() => {
              if (projectId) {
                const layer = layers.find((l) => l.id === contextMenu.layerId);
                if (layer) {
                  updateLayer.mutate({
                    projectId,
                    layerId: contextMenu.layerId,
                    data: { opacity: Math.min(1, layer.opacity + 0.1) },
                  });
                }
              }
              setContextMenu(null);
            }}
            className="w-full px-3 py-1.5 text-left text-sm text-slate-300 hover:bg-slate-700"
          >
            Increase Opacity
          </button>
          <div className="border-t border-slate-700 my-1" />
          <button
            onClick={() => {
              if (projectId && confirm("Delete this layer?")) {
                deleteLayer.mutate(
                  { projectId, layerId: contextMenu.layerId },
                  {
                    onSuccess: () => toast.success("Layer deleted"),
                    onError: (err) => toast.error(getErrorMessage(err)),
                  }
                );
              }
              setContextMenu(null);
            }}
            className="w-full px-3 py-1.5 text-left text-sm text-red-400 hover:bg-slate-700"
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
}
