import { useWorkspaceStore } from "../../store/useWorkspaceStore";
import { useLayers } from "../../hooks/useGeospatial";
import { useAOIs } from "../../hooks/useGeospatial";
import { useProject } from "../../hooks/useProjects";
import LoadingState from "../ui/LoadingState";

interface PropertiesPanelProps {
  projectId: string | undefined;
}

export default function PropertiesPanel({ projectId }: PropertiesPanelProps) {
  const { selectedLayerId, selectedObjectId } = useWorkspaceStore();
  const { data: layers = [] } = useLayers(projectId || null);
  const { data: aois = [] } = useAOIs(projectId || null);
  const { data: project, isLoading } = useProject(projectId || null);

  const selectedLayer = layers.find((l) => l.id === selectedLayerId);
  const selectedAOI = aois.find((a) => a.id === selectedObjectId);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatArea = (m2: number | null) => {
    if (m2 === null || m2 === undefined) return "N/A";
    if (m2 > 1000000) return `${(m2 / 1000000).toFixed(2)} km²`;
    return `${m2.toFixed(1)} m²`;
  };

  if (isLoading && !selectedObjectId && !selectedLayerId) {
    return (
      <div className="flex flex-col h-full">
        <div className="p-3 border-b border-slate-700">
          <h3 className="font-semibold text-white text-sm">Properties</h3>
        </div>
        <div className="flex-1">
          <LoadingState compact label="Loading properties..." />
        </div>
      </div>
    );
  }

  let content: { title: string; fields: { label: string; value: string }[] } | null = null;

  if (selectedAOI) {
    content = {
      title: selectedAOI.name,
      fields: [
        { label: "UUID", value: selectedAOI.id },
        { label: "Type", value: selectedAOI.geometry_type || "N/A" },
        { label: "Area", value: formatArea(selectedAOI.area_m2) },
        { label: "Source", value: selectedAOI.source || "N/A" },
        { label: "Fill Color", value: selectedAOI.fill_color },
        { label: "Stroke Color", value: selectedAOI.stroke_color },
        { label: "Created", value: formatDate(selectedAOI.created_at) },
        { label: "Modified", value: formatDate(selectedAOI.updated_at) },
        ...(selectedAOI.description ? [{ label: "Description", value: selectedAOI.description }] : []),
      ],
    };
  } else if (selectedLayer) {
    let metadata: Record<string, any> = {};
    if (selectedLayer.metadata) {
      try {
        metadata = JSON.parse(selectedLayer.metadata);
      } catch (e) {
        console.warn("Invalid metadata JSON", e);
      }
    }
    content = {
      title: selectedLayer.name,
      fields: [
        { label: "UUID", value: selectedLayer.id },
        { label: "Type", value: selectedLayer.layer_type },
        { label: "Visible", value: selectedLayer.visible ? "Yes" : "No" },
        { label: "Opacity", value: `${Math.round(selectedLayer.opacity * 100)}%` },
        { label: "Z-Index", value: String(selectedLayer.z_index) },
        { label: "Source Type", value: selectedLayer.source_type || "N/A" },
        { label: "Source ID", value: selectedLayer.source_id || "N/A" },
        { label: "Created", value: formatDate(selectedLayer.created_at) },
        { label: "Modified", value: formatDate(selectedLayer.updated_at) },
        ...Object.entries(metadata).map(([k, v]) => ({
          label: k,
          value: typeof v === "object" ? JSON.stringify(v) : String(v),
        })),
      ],
    };
  } else if (project) {
    content = {
      title: project.name,
      fields: [
        { label: "UUID", value: project.id },
        { label: "Status", value: project.status },
        { label: "CRS", value: project.coordinate_system || "EPSG:4326" },
        { label: "Version", value: project.project_version },
        { label: "Created", value: formatDate(project.created_at) },
        { label: "Modified", value: formatDate(project.updated_at) },
        { label: "Last Opened", value: formatDate(project.last_opened_at) },
        ...(project.description ? [{ label: "Description", value: project.description }] : []),
        ...(project.area_of_interest ? [{ label: "AOI", value: project.area_of_interest }] : []),
      ],
    };
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-slate-700">
        <h3 className="font-semibold text-white text-sm">Properties</h3>
      </div>
      <div className="flex-1 overflow-y-auto">
        {content ? (
          <div className="p-3">
            <h4 className="text-sm font-medium text-primary-400 mb-3">{content.title}</h4>
            <div className="space-y-2">
              {content.fields.map((field) => (
                <div key={field.label} className="flex flex-col">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                    {field.label}
                  </span>
                  <span className="text-xs text-white font-mono break-all">
                    {field.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-4 text-center text-slate-400 text-sm">
            Select an object to view properties
          </div>
        )}
      </div>
    </div>
  );
}
