import { useParams, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import AssetList from "../components/assets/AssetList";
import AssetDetails from "../components/assets/AssetDetails";
import AssetImport from "../components/assets/AssetImport";
import AssetFilter from "../components/assets/AssetFilter";
import AssetStats from "../components/assets/AssetStats";
import CollectionList from "../components/assets/CollectionList";
import { useAssetStore } from "../store/useAssetStore";
import EmptyState from "../components/ui/EmptyState";
import Breadcrumbs from "../components/ui/Breadcrumbs";

export default function AssetLibrary() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { setProjectId, viewMode, setViewMode } = useAssetStore();

  useEffect(() => {
    setProjectId(id || null);
  }, [id, setProjectId]);

  if (!id) {
    return (
      <div className="p-6">
        <EmptyState
          title="No project selected"
          description="Open a project to view and manage its assets."
          action={
            <button
              onClick={() => navigate("/projects")}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
            >
              Go to Projects
            </button>
          }
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-2 border-b border-slate-700/50 shrink-0">
        <Breadcrumbs
          items={[
            { label: "Projects", to: "/projects" },
            { label: "Project", to: `/projects/${id}` },
            { label: "Assets" },
          ]}
        />
      </div>
      <div className="flex flex-1 min-h-0">
      {/* Left sidebar - Import, Filter, Collections */}
      <div className="w-72 border-r flex flex-col overflow-auto">
        <div className="p-3 border-b">
          <h2 className="font-semibold text-white">Asset Library</h2>
        </div>
        <AssetImport />
        <AssetFilter />
        <div className="p-3 border-t">
          <AssetStats />
        </div>
        <div className="border-t">
          <CollectionList />
        </div>
      </div>

      {/* Center - Asset List */}
      <div className="w-96 border-r flex flex-col overflow-hidden">
        <div className="p-3 border-b flex items-center justify-between">
          <span className="text-sm text-slate-400">Assets</span>
          <div className="flex gap-1">
            <button
              onClick={() => setViewMode("grid")}
              className={`px-2 py-1 text-xs rounded ${viewMode === "grid" ? "bg-primary-600 text-white" : "bg-slate-700/50 text-slate-400"}`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`px-2 py-1 text-xs rounded ${viewMode === "list" ? "bg-primary-600 text-white" : "bg-slate-700/50 text-slate-400"}`}
            >
              List
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-auto">
          <AssetList />
        </div>
      </div>

      {/* Right - Details */}
      <div className="flex-1 overflow-auto">
        <AssetDetails />
      </div>
      </div>
    </div>
  );
}
