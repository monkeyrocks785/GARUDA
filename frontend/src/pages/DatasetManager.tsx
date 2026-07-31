import { useParams, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import DatasetList from "../components/datasets/DatasetList";
import DatasetDetails from "../components/datasets/DatasetDetails";
import DatasetImport from "../components/datasets/DatasetImport";
import DatasetFilter from "../components/datasets/DatasetFilter";
import DatasetStats from "../components/datasets/DatasetStats";
import { useDatasetStore } from "../store/useDatasetStore";
import EmptyState from "../components/ui/EmptyState";
import Breadcrumbs from "../components/ui/Breadcrumbs";

export default function DatasetManager() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { setProjectId } = useDatasetStore();

  useEffect(() => {
    setProjectId(id || null);
  }, [id, setProjectId]);

  if (!id) {
    return (
      <div className="p-6">
        <EmptyState
          title="No project selected"
          description="Open a project to view and manage its datasets."
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
            { label: "Datasets" },
          ]}
        />
      </div>
      <div className="flex flex-1 min-h-0">
      {/* Left sidebar - Import and Filter */}
      <div className="w-72 border-r flex flex-col">
        <div className="p-3 border-b">
          <h2 className="font-semibold">Datasets</h2>
        </div>
        <DatasetImport />
        <DatasetFilter />
        <div className="p-3">
          <DatasetStats />
        </div>
      </div>

      {/* Center - Dataset List */}
      <div className="w-96 border-r overflow-auto">
        <DatasetList />
      </div>

      {/* Right - Details */}
      <div className="flex-1 overflow-auto">
        <DatasetDetails />
      </div>
      </div>
    </div>
  );
}
