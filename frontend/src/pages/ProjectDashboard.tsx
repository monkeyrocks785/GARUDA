import { useParams, useNavigate } from "react-router-dom";
import { useProject, useOpenProject } from "../hooks/useProjects";
import { useDatasets } from "../hooks/useDatasets";
import { useAOIs } from "../hooks/useGeospatial";
import { usePipelines } from "../hooks/usePipelines";
import { useAssets } from "../hooks/useAssets";
import { useDatasetStore } from "../store/useDatasetStore";
import { usePipelineStore } from "../store/usePipelineStore";
import { useAssetStore } from "../store/useAssetStore";
import { useEffect, useRef } from "react";
import { formatDate as formatDateTime } from "../utils/format";
import { parseTagArray } from "../utils/json";

const statusColors: Record<string, string> = {
  created: "bg-slate-500/20 text-slate-400",
  active: "bg-green-500/20 text-green-400",
  processing: "bg-blue-500/20 text-blue-400",
  completed: "bg-emerald-500/20 text-emerald-400",
  failed: "bg-red-500/20 text-red-400",
  archived: "bg-gray-500/20 text-gray-400",
};

const stageLabels: Record<string, string> = {
  initialization: "Initializing",
  data_acquisition: "Data Acquisition",
  processing: "Processing",
  analysis: "Analysis",
  reporting: "Reporting",
};

export default function ProjectDashboard() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: project, isLoading, error } = useProject(id || null);
  const openProject = useOpenProject();

  // Set project IDs in stores so child hooks can fetch data
  const setDatasetProjectId = useDatasetStore((s) => s.setProjectId);
  const setPipelineProjectId = usePipelineStore((s) => s.setProjectId);
  const setAssetProjectId = useAssetStore((s) => s.setProjectId);

  useEffect(() => {
    if (id) {
      setDatasetProjectId(id);
      setPipelineProjectId(id);
      setAssetProjectId(id);
    }
  }, [id, setDatasetProjectId, setPipelineProjectId, setAssetProjectId]);

  // Fetch related data counts
  const { data: datasetsData, isLoading: loadingDatasets } = useDatasets();
  const { data: aois, isLoading: loadingAois } = useAOIs(id || null);
  const { data: pipelinesData, isLoading: loadingPipelines } = usePipelines();
  const { data: assetsData, isLoading: loadingAssets } = useAssets();

  // Mark project as opened (only once per project id)
  const openedProjectRef = useRef<string | null>(null);
  useEffect(() => {
    if (id && openedProjectRef.current !== id) {
      openedProjectRef.current = id;
      openProject.mutate(id);
    }
  }, [id, openProject]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500 mb-4"></div>
        <p className="text-slate-400">Loading project...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="text-center py-24">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/10 flex items-center justify-center">
          <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">Failed to load project</h2>
        <p className="text-slate-400 mb-6">{error instanceof Error ? error.message : "An unexpected error occurred"}</p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-slate-700/50 hover:bg-slate-600/50 text-white rounded-lg transition-colors"
          >
            Retry
          </button>
          <button
            onClick={() => navigate("/projects")}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
          >
            Back to Projects
          </button>
        </div>
      </div>
    );
  }

  // Not found state
  if (!project) {
    return (
      <div className="text-center py-24">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700/50 flex items-center justify-center">
          <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">Project not found</h2>
        <p className="text-slate-400 mb-6">The project you're looking for doesn't exist or may have been deleted.</p>
        <button
          onClick={() => navigate("/projects")}
          className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          Back to Projects
        </button>
      </div>
    );
  }

  const datasetCount = datasetsData?.total ?? 0;
  const aoiCount = aois?.length ?? 0;
  const pipelineCount = pipelinesData?.total ?? 0;
  const assetCount = assetsData?.total ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => navigate("/projects")}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-white">{project.name}</h1>
            <span className={`px-2 py-1 text-xs rounded-full ${statusColors[project.status] || "bg-slate-500/20 text-slate-400"}`}>
              {project.status}
            </span>
            {project.favorite && (
              <span className="text-yellow-400 text-sm">★ Favorite</span>
            )}
          </div>
          {project.description && (
            <p className="text-slate-400 ml-12">{project.description}</p>
          )}
          <p className="text-slate-500 text-xs ml-12 mt-1">ID: {project.id}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(`/projects/${id}/datasets`)}
            className="px-4 py-2 bg-slate-700/50 hover:bg-slate-600/50 text-white rounded-lg transition-colors"
          >
            Datasets
          </button>
          <button
            onClick={() => navigate(`/projects/${id}/assets`)}
            className="px-4 py-2 bg-slate-700/50 hover:bg-slate-600/50 text-white rounded-lg transition-colors"
          >
            Assets
          </button>
          <button
            onClick={() => navigate(`/projects/${id}/pipelines`)}
            className="px-4 py-2 bg-slate-700/50 hover:bg-slate-600/50 text-white rounded-lg transition-colors"
          >
            Pipelines
          </button>
          <button
            onClick={() => navigate(`/projects/${id}/queries`)}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
          >
            Queries
          </button>
          <button
            onClick={() => navigate(`/projects/${id}/gis`)}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
          >
            Open Map
          </button>
        </div>
      </div>

      {/* Progress */}
      {project.progress > 0 && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4">
          <div className="flex justify-between text-sm text-slate-400 mb-2">
            <span>Current Stage: {stageLabels[project.current_stage || ""] || project.current_stage || "N/A"}</span>
            <span>{Math.round(project.progress)}% Complete</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${project.progress}%` }}
            />
          </div>
          {project.current_task && (
            <p className="text-sm text-slate-400 mt-2">Current Task: {project.current_task}</p>
          )}
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">
            {loadingDatasets ? "…" : datasetCount}
          </p>
          <p className="text-xs text-slate-400">Datasets</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{loadingAois ? "…" : aoiCount}</p>
          <p className="text-xs text-slate-400">AOIs</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">
            {loadingPipelines ? "…" : pipelineCount}
          </p>
          <p className="text-xs text-slate-400">Pipelines</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{loadingAssets ? "…" : assetCount}</p>
          <p className="text-xs text-slate-400">Assets</p>
        </div>
      </div>

      {/* Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Overview Widget */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Overview</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-400">Created</span>
              <span className="text-white">{formatDateTime(project.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Last Updated</span>
              <span className="text-white">{formatDateTime(project.updated_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Last Opened</span>
              <span className="text-white">{formatDateTime(project.last_opened_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Version</span>
              <span className="text-white">{project.project_version}</span>
            </div>
            {project.area_of_interest && (
              <div className="flex justify-between">
                <span className="text-slate-400">Area of Interest</span>
                <span className="text-white">{project.area_of_interest}</span>
              </div>
            )}
            {project.coordinate_system && (
              <div className="flex justify-between">
                <span className="text-slate-400">Coordinate System</span>
                <span className="text-white">{project.coordinate_system}</span>
              </div>
            )}
          </div>
        </div>

        {/* Current Processing Widget */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Processing Status</h3>
          {project.is_processing ? (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
                <span className="text-white font-medium">Processing...</span>
              </div>
              {project.last_job_id && (
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Job ID</span>
                    <span className="text-white text-sm font-mono">{project.last_job_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Status</span>
                    <span className="text-blue-400 text-sm">{project.last_job_status}</span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-slate-500"></span>
                <span className="text-slate-400">Idle</span>
              </div>
              {project.last_job_status && (
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Last Job Status</span>
                    <span className={`text-sm ${
                      project.last_job_status === "completed" ? "text-green-400" :
                      project.last_job_status === "failed" ? "text-red-400" : "text-slate-400"
                    }`}>{project.last_job_status}</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Recent Activity Widget */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          <div className="text-slate-400 text-sm">
            <p>No recent activity to display.</p>
          </div>
        </div>

        {/* Reports Widget */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Reports</h3>
          <div className="text-slate-400 text-sm">
            <p>No reports generated yet.</p>
          </div>
        </div>
      </div>

      {/* Tags */}
      {parseTagArray(project.tags).length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Tags</h3>
          <div className="flex flex-wrap gap-2">
            {parseTagArray(project.tags).map((tag, i) => (
              <span key={i} className="px-3 py-1 text-sm bg-slate-700/50 text-slate-300 rounded-full">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Notes</h3>
        {project.notes ? (
          <p className="text-slate-300 whitespace-pre-wrap">{project.notes}</p>
        ) : (
          <p className="text-slate-400 text-sm">No notes added yet.</p>
        )}
      </div>
    </div>
  );
}
