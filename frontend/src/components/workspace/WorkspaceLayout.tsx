import { useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useWorkspaceStore } from "../../store/useWorkspaceStore";
import { useWorkspaceState, useUpdateWorkspace } from "../../hooks/useWorkspace";
import MapCanvas from "./MapCanvas";
import ProjectExplorer from "./ProjectExplorer";
import LayerManager from "./LayerManager";
import PropertiesPanel from "./PropertiesPanel";
import DrawingToolbar from "./DrawingToolbar";
import StatusBar from "./StatusBar";
import { BASEMAPS } from "../../types/workspace";

function useAutoSave(projectId: string | null) {
  const updateWorkspace = useUpdateWorkspace();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const save = useCallback(() => {
    if (!projectId) return;
    const state = useWorkspaceStore.getState();
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      updateWorkspace.mutate({
        projectId,
        data: {
          zoom: state.zoom,
          center_lat: state.center[0],
          center_lng: state.center[1],
          map_rotation: state.mapRotation,
          basemap: state.basemap,
          active_tool: state.activeTool,
          selected_layer_id: state.selectedLayerId ?? undefined,
          panel_layout: JSON.stringify(state.panelLayout),
        },
      });
    }, 2000);
  }, [projectId, updateWorkspace]);

  return save;
}

export default function WorkspaceLayout() {
  const { id: projectId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: workspaceState } = useWorkspaceState(projectId || null);

  const {
    zoom,
    center,
    mapRotation,
    basemap,
    activeTool,
    panelLayout,
    setZoom,
    setCenter,
    setMapRotation,
    setBasemap,
    setActiveTool,
    setPanelLayout,
    togglePanel,
    setPanelWidth,
    setMousePosition,
    setMeasurementResult,
  } = useWorkspaceStore();

  const saveWorkspace = useAutoSave(projectId || null);

  // Restore workspace from backend
  useEffect(() => {
    if (workspaceState) {
      useWorkspaceStore.setState({
        zoom: workspaceState.zoom,
        center: [workspaceState.center_lat, workspaceState.center_lng],
        mapRotation: workspaceState.map_rotation,
        basemap: workspaceState.basemap || "osm",
        activeTool: workspaceState.active_tool || "pan",
        selectedLayerId: workspaceState.selected_layer_id,
      });
      if (workspaceState.panel_layout) {
        try {
          const layout = JSON.parse(workspaceState.panel_layout);
          setPanelLayout(layout);
        } catch (e) {
          console.warn("Invalid panel_layout JSON", e);
        }
      }
    }
  }, [workspaceState, setPanelLayout]);

  // Auto-save on state changes
  useEffect(() => {
    saveWorkspace();
    // saveWorkspace identity is unstable (wraps a useMutation); track state only
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoom, center, mapRotation, basemap, activeTool, panelLayout]);

  // Reset on unmount
  useEffect(() => {
    return () => {
      setMousePosition(null);
      setMeasurementResult(null);
    };
  }, [setMousePosition, setMeasurementResult]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.ctrlKey && e.key === "z") {
        e.preventDefault();
        useWorkspaceStore.getState().undo();
      } else if (e.ctrlKey && e.key === "y") {
        e.preventDefault();
        useWorkspaceStore.getState().redo();
      } else {
        const toolMap: Record<string, string> = {
          h: "pan",
          p: "draw_point",
          l: "draw_line",
          g: "draw_polygon",
          r: "draw_rectangle",
          c: "draw_circle",
          d: "measure_distance",
          a: "measure_area",
          b: "measure_bearing",
          e: "edit_shape",
          x: "delete_shape",
        };
        if (toolMap[e.key.toLowerCase()]) {
          setActiveTool(toolMap[e.key.toLowerCase()]);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setActiveTool]);

  const handleDragEnd = (
    panelId: string,
    e: React.MouseEvent
  ) => {
    const startX = e.clientX;
    const startWidth = panelLayout[panelId]?.width || 280;
    const isRight = panelLayout[panelId]?.position === "right";

    const onMove = (ev: MouseEvent) => {
      const dx = ev.clientX - startX;
      const newWidth = isRight ? startWidth - dx : startWidth + dx;
      setPanelWidth(panelId, Math.max(180, Math.min(600, newWidth)));
    };
    const onUp = () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  const showExplorer = panelLayout.projectExplorer?.visible !== false;
  const showLayers = panelLayout.layerManager?.visible !== false;
  const showProps = panelLayout.propertiesPanel?.visible !== false;
  const explorerWidth = panelLayout.projectExplorer?.width || 260;
  const layersWidth = panelLayout.layerManager?.width || 280;
  const propsWidth = panelLayout.propertiesPanel?.width || 300;

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Top Toolbar */}
      <div className="bg-slate-800 border-b border-slate-700 px-3 py-1.5 flex items-center gap-2">
        {/* Back button */}
        <button
          onClick={() => navigate("/projects")}
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors"
          title="Back to Projects"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="w-px h-5 bg-slate-600" />

        {/* Basemap selector */}
        <select
          value={basemap}
          onChange={(e) => setBasemap(e.target.value)}
          className="px-2 py-1 bg-slate-700 border border-slate-600 rounded text-xs text-white focus:outline-none focus:border-primary-500"
        >
          {BASEMAPS.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>

        <div className="w-px h-5 bg-slate-600" />

        {/* Navigation tools */}
        <button
          onClick={() => setActiveTool("pan")}
          className={`p-1.5 rounded transition-colors ${
            activeTool === "pan" ? "bg-primary-600 text-white" : "text-slate-400 hover:bg-slate-700 hover:text-white"
          }`}
          title="Pan (H)"
        >
          🖐️
        </button>
        <button
          onClick={() => {
            setZoom(2);
            setCenter([20, 0]);
            setMapRotation(0);
          }}
          className="p-1.5 text-slate-400 hover:bg-slate-700 hover:text-white rounded transition-colors"
          title="Reset View"
        >
          🏠
        </button>

        <div className="w-px h-5 bg-slate-600" />

        {/* Zoom controls */}
        <button
          onClick={() => setZoom(Math.min(24, zoom + 1))}
          className="p-1.5 text-slate-400 hover:bg-slate-700 hover:text-white rounded transition-colors"
          title="Zoom In"
        >
          +
        </button>
        <span className="text-xs text-white font-mono w-10 text-center">{zoom.toFixed(1)}</span>
        <button
          onClick={() => setZoom(Math.max(0, zoom - 1))}
          className="p-1.5 text-slate-400 hover:bg-slate-700 hover:text-white rounded transition-colors"
          title="Zoom Out"
        >
          -
        </button>

        <div className="w-px h-5 bg-slate-600" />

        {/* Rotation */}
        <button
          onClick={() => setMapRotation(mapRotation - Math.PI / 6)}
          className="p-1.5 text-slate-400 hover:bg-slate-700 hover:text-white rounded transition-colors text-xs"
          title="Rotate Left"
        >
          ↺
        </button>
        <button
          onClick={() => setMapRotation(0)}
          className="p-1.5 text-slate-400 hover:bg-slate-700 hover:text-white rounded transition-colors text-xs"
          title="Reset Rotation"
        >
          0°
        </button>
        <button
          onClick={() => setMapRotation(mapRotation + Math.PI / 6)}
          className="p-1.5 text-slate-400 hover:bg-slate-700 hover:text-white rounded transition-colors text-xs"
          title="Rotate Right"
        >
          ↻
        </button>

        <div className="flex-1" />

        {/* Panel toggles */}
        <button
          onClick={() => togglePanel("projectExplorer")}
          className={`p-1.5 rounded transition-colors ${
            showExplorer ? "bg-primary-600 text-white" : "text-slate-400 hover:bg-slate-700 hover:text-white"
          }`}
          title="Toggle Project Explorer"
        >
          📁
        </button>
        <button
          onClick={() => togglePanel("layerManager")}
          className={`p-1.5 rounded transition-colors ${
            showLayers ? "bg-primary-600 text-white" : "text-slate-400 hover:bg-slate-700 hover:text-white"
          }`}
          title="Toggle Layer Manager"
        >
          🗺️
        </button>
        <button
          onClick={() => togglePanel("propertiesPanel")}
          className={`p-1.5 rounded transition-colors ${
            showProps ? "bg-primary-600 text-white" : "text-slate-400 hover:bg-slate-700 hover:text-white"
          }`}
          title="Toggle Properties Panel"
        >
          📋
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panels */}
        {showExplorer && (
          <div
            className="bg-slate-800 border-r border-slate-700 overflow-y-auto flex-shrink-0 relative"
            style={{ width: explorerWidth }}
          >
            <ProjectExplorer projectId={projectId} />
            <div
              className="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-primary-500/50 transition-colors z-10"
              onMouseDown={(e) => handleDragEnd("projectExplorer", e)}
            />
          </div>
        )}

        {showLayers && (
          <div
            className="bg-slate-800 border-r border-slate-700 overflow-y-auto flex-shrink-0 relative"
            style={{ width: layersWidth }}
          >
            <LayerManager projectId={projectId} />
            <div
              className="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-primary-500/50 transition-colors z-10"
              onMouseDown={(e) => handleDragEnd("layerManager", e)}
            />
          </div>
        )}

        {/* Map Canvas */}
        <div className="flex-1 relative">
          <MapCanvas projectId={projectId} />
          <DrawingToolbar />
        </div>

        {/* Right panel */}
        {showProps && (
          <div
            className="bg-slate-800 border-l border-slate-700 overflow-y-auto flex-shrink-0 relative"
            style={{ width: propsWidth }}
          >
            <PropertiesPanel projectId={projectId} />
            <div
              className="absolute top-0 left-0 w-1 h-full cursor-col-resize hover:bg-primary-500/50 transition-colors z-10"
              onMouseDown={(e) => handleDragEnd("propertiesPanel", e)}
            />
          </div>
        )}
      </div>

      {/* Status Bar */}
      <StatusBar projectId={projectId} />
    </div>
  );
}
