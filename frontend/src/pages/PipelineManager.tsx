import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useNodeTypes } from "../hooks/usePipelines";
import { usePipelineStore } from "../store/usePipelineStore";
import PipelineList from "../components/pipelines/PipelineList";
import PipelineDetails from "../components/pipelines/PipelineDetails";
import QueueView from "../components/pipelines/QueueView";
import CreatePipeline from "../components/pipelines/CreatePipeline";
import PipelineStats from "../components/pipelines/PipelineStats";
import Breadcrumbs from "../components/ui/Breadcrumbs";
import type { NodeType } from "../types/pipeline";

export default function PipelineManager() {
  const { id: projectId } = useParams<{ id: string }>();
  const { view, setView, setProjectId } = usePipelineStore();
  const { data: nodeTypes, isLoading: loadingNodeTypes } = useNodeTypes();

  useEffect(() => {
    if (projectId) {
      setProjectId(projectId);
    }
  }, [projectId, setProjectId]);

  return (
    <div className="h-full flex flex-col bg-slate-900">
      <div className="px-4 py-2 border-b border-slate-700/50 shrink-0">
        <Breadcrumbs
          items={[
            { label: "Projects", to: "/projects" },
            { label: "Project", to: `/projects/${projectId}` },
            { label: "Pipelines" },
          ]}
        />
      </div>
      <div className="flex flex-1 min-h-0">
      {/* Sidebar */}
      <div className="w-72 border-r border-slate-700/50 flex flex-col">
        <div className="p-3 border-b border-slate-700/50 flex items-center justify-between">
          <h1 className="text-lg font-bold text-white">Pipelines</h1>
          <div className="flex gap-1">
            <button
              onClick={() => setView("list")}
              className={`px-2 py-1 text-xs rounded ${view === "list" || view === "detail" ? "bg-primary-600 text-white" : "bg-slate-700/50 text-slate-400"}`}
            >
              Pipelines
            </button>
            <button
              onClick={() => setView("queue")}
              className={`px-2 py-1 text-xs rounded ${view === "queue" ? "bg-primary-600 text-white" : "bg-slate-700/50 text-slate-400"}`}
            >
              Queue
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {view === "queue" ? <div className="p-4 text-sm text-slate-400">Pipeline queue is shown in the main area. Select Pipelines to browse project pipelines.</div> : <PipelineList />}
        </div>
        {view !== "queue" && <CreatePipeline />}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        {view === "queue" ? (
          <QueueView />
        ) : (
          <PipelineDetails />
        )}
      </div>

      {/* Stats Panel */}
      <div className="w-48 border-l border-slate-700/50 bg-slate-800/30">
        <PipelineStats />
        {/* Node Types */}
        <div className="p-3 border-t border-slate-700/50">
          <span className="text-xs font-semibold text-slate-400 uppercase">Node Types</span>
          <div className="mt-2 space-y-1">
            {loadingNodeTypes ? (
              <div className="text-xs text-slate-500">Loading...</div>
            ) : (
              (nodeTypes || []).map((nt: NodeType) => (
                <div key={nt.type} className="text-xs text-slate-400">
                  <span className="text-primary-400">{nt.type}</span>
                  <p className="text-slate-600 text-[10px] mt-0.5">{nt.description}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}
