import { useWorkspaceStore } from "../../store/useWorkspaceStore";
import { useLayers } from "../../hooks/useGeospatial";
import { useProject } from "../../hooks/useProjects";

interface StatusBarProps {
  projectId: string | undefined;
}

export default function StatusBar({ projectId }: StatusBarProps) {
  const { mousePosition, zoom, activeTool, measurementResult, basemap } =
    useWorkspaceStore();
  const { data: layers = [] } = useLayers(projectId || null);
  const { data: project } = useProject(projectId || null);

  return (
    <div className="bg-slate-800 border-t border-slate-700 px-3 py-1 flex items-center justify-between text-[11px] text-slate-400 select-none">
      {/* Left: Mouse coordinates */}
      <div className="flex items-center gap-4">
        <span>
          Lat:{" "}
          <span className="text-white font-mono">
            {mousePosition ? mousePosition[0].toFixed(6) : "---"}
          </span>
        </span>
        <span>
          Lon:{" "}
          <span className="text-white font-mono">
            {mousePosition ? mousePosition[1].toFixed(6) : "---"}
          </span>
        </span>
        <span>
          CRS: <span className="text-white">EPSG:4326</span>
        </span>
      </div>

      {/* Center: Measurement / tool */}
      <div className="flex items-center gap-4">
        {measurementResult && (
          <span className="text-primary-400 font-medium">{measurementResult}</span>
        )}
        <span>
          Tool:{" "}
          <span className="text-white capitalize">
            {activeTool.replace(/_/g, " ")}
          </span>
        </span>
      </div>

      {/* Right: Zoom, layers, basemap, project */}
      <div className="flex items-center gap-4">
        <span>
          Zoom: <span className="text-white font-mono">{zoom.toFixed(1)}</span>
        </span>
        <span>
          Layers: <span className="text-white">{layers.length}</span>
        </span>
        <span>
          Basemap:{" "}
          <span className="text-white capitalize">
            {basemap?.replace(/_/g, " ") || "None"}
          </span>
        </span>
        {project && (
          <span className="text-slate-500">
            {project.name}
          </span>
        )}
      </div>
    </div>
  );
}
