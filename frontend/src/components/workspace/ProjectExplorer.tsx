import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useProject } from "../../hooks/useProjects";
import { useAOIs } from "../../hooks/useGeospatial";
import { useLayers } from "../../hooks/useGeospatial";
import { useDatasets } from "../../hooks/useDatasets";
import { useAssets } from "../../hooks/useAssets";
import { usePipelines } from "../../hooks/usePipelines";
import { useWorkspaceStore } from "../../store/useWorkspaceStore";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";
import { getErrorMessage } from "../../utils/errorMessage";

interface ProjectExplorerProps {
  projectId: string | undefined;
}

interface TreeNode {
  id: string;
  label: string;
  icon: string;
  type: "project" | "mission" | "aois" | "datasets" | "assets" | "reports" | "pipelines" | "collections" | "item";
  children?: TreeNode[];
  data?: any;
}

function TreeItem({
  node,
  depth = 0,
}: {
  node: TreeNode;
  depth?: number;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const { setSelectedObjectId, setSelectedObjectType } = useWorkspaceStore();

  const handleDoubleClick = () => {
    if (node.type === "project") {
      // Already in project
    } else if (node.type === "item" && node.data) {
      setSelectedObjectId(node.data.id);
      setSelectedObjectType(node.type);
    }
  };

  return (
    <div>
      <div
        className="flex items-center gap-1 py-1 px-2 hover:bg-slate-700/50 rounded cursor-pointer text-sm"
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => {
          if (node.children) setExpanded(!expanded);
          if (node.type === "item" && node.data) {
            setSelectedObjectId(node.data.id);
            setSelectedObjectType(node.type);
          }
        }}
        onDoubleClick={handleDoubleClick}
      >
        {node.children ? (
          <svg
            className={`w-3 h-3 text-slate-400 transition-transform ${
              expanded ? "rotate-90" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        ) : (
          <span className="w-3" />
        )}
        <span className="text-sm">{node.icon}</span>
        <span className="text-slate-300 truncate">{node.label}</span>
      </div>
      {expanded &&
        node.children?.map((child) => (
          <TreeItem key={child.id} node={child} depth={depth + 1} />
        ))}
    </div>
  );
}

export default function ProjectExplorer({ projectId }: ProjectExplorerProps) {
  const { data: project, isLoading, isError, error, refetch } = useProject(projectId || null);
  const { data: aois = [] } = useAOIs(projectId || null);
  const { data: layers = [] } = useLayers(projectId || null);
  const { data: datasetsData } = useDatasets();
  const { data: assetsData } = useAssets();
  const { data: pipelinesData } = usePipelines();
  const navigate = useNavigate();

  if (!projectId) {
    return (
      <div className="p-4 text-center text-slate-400 text-sm">
        No project loaded
      </div>
    );
  }

  if (isLoading) {
    return <LoadingState compact label="Loading project..." />;
  }

  if (isError) {
    return (
      <ErrorState
        compact
        title="Failed to load project"
        message={getErrorMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  if (!project) {
    return (
      <div className="p-4 text-center text-slate-400 text-sm">
        No project loaded
      </div>
    );
  }

  const datasets = datasetsData?.datasets || [];
  const assets = assetsData?.assets || [];
  const pipelines = pipelinesData?.pipelines || [];

  const tree: TreeNode = {
    id: project.id,
    label: project.name,
    icon: "📁",
    type: "project",
    children: [
      {
        id: "aois",
        label: "Areas of Interest",
        icon: "🎯",
        type: "aois",
        children: aois.map((aoi) => ({
          id: aoi.id,
          label: aoi.name,
          icon: "📐",
          type: "item" as const,
          data: aoi,
        })),
      },
      {
        id: "layers",
        label: "Layers",
        icon: "🗺️",
        type: "project",
        children: layers.map((layer) => ({
          id: layer.id,
          label: layer.name,
          icon: layer.layer_type === "raster" ? "🖼️" : "📍",
          type: "item" as const,
          data: layer,
        })),
      },
      {
        id: "datasets",
        label: "Datasets",
        icon: "📊",
        type: "datasets",
        children: datasets.map((ds) => ({
          id: ds.id,
          label: ds.name,
          icon: "📄",
          type: "item" as const,
          data: ds,
        })),
      },
      {
        id: "assets",
        label: "Assets",
        icon: "📦",
        type: "assets",
        children: assets.map((asset) => ({
          id: asset.id,
          label: asset.display_name || asset.name,
          icon: "📎",
          type: "item" as const,
          data: asset,
        })),
      },
      {
        id: "pipelines",
        label: "Pipelines",
        icon: "⚙️",
        type: "pipelines",
        children: pipelines.map((p) => ({
          id: p.id,
          label: p.name,
          icon: "🔄",
          type: "item" as const,
          data: p,
        })),
      },
      {
        id: "reports",
        label: "Reports",
        icon: "📋",
        type: "reports",
        children: [],
      },
      {
        id: "collections",
        label: "Collections",
        icon: "📂",
        type: "collections",
        children: [],
      },
    ],
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-slate-700">
        <h3 className="font-semibold text-white text-sm">Project Explorer</h3>
      </div>
      <div className="flex-1 overflow-y-auto py-1">
        <TreeItem node={tree} />
      </div>
      <div className="p-2 border-t border-slate-700 space-y-1">
        <button
          onClick={() => navigate(`/projects/${projectId}/datasets`)}
          className="w-full px-2 py-1.5 text-xs text-slate-400 hover:bg-slate-700/50 rounded text-left"
        >
          Open Dataset Manager
        </button>
        <button
          onClick={() => navigate(`/projects/${projectId}/assets`)}
          className="w-full px-2 py-1.5 text-xs text-slate-400 hover:bg-slate-700/50 rounded text-left"
        >
          Open Asset Library
        </button>
        <button
          onClick={() => navigate(`/projects/${projectId}/pipelines`)}
          className="w-full px-2 py-1.5 text-xs text-slate-400 hover:bg-slate-700/50 rounded text-left"
        >
          Open Pipeline Manager
        </button>
      </div>
    </div>
  );
}
