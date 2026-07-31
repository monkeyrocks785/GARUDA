import { usePipelines } from "../../hooks/usePipelines";
import { usePipelineStore } from "../../store/usePipelineStore";
import type { Pipeline } from "../../types/pipeline";
import { STATUS_COLORS } from "../../types/pipeline";
import { getErrorMessage } from "../../utils/errorMessage";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";
import EmptyState from "../ui/EmptyState";

function formatMs(ms: number): string {
  if (ms === 0) return "-";
  if (ms < 1000) return `${ms}ms`;
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)}s`;
  return `${(s / 60).toFixed(1)}m`;
}

export default function PipelineList() {
  const { data, isLoading, isError, error, refetch } = usePipelines();
  const { selectedPipelineId, setSelectedPipelineId, setView } = usePipelineStore();

  if (isLoading) {
    return <LoadingState compact label="Loading pipelines..." />;
  }

  if (isError) {
    return (
      <ErrorState
        compact
        title="Failed to load pipelines"
        message={getErrorMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  const pipelines = data?.pipelines || [];

  if (pipelines.length === 0) {
    return (
      <EmptyState
        compact
        title="No pipelines yet"
        description="Create a pipeline to get started"
      />
    );
  }

  return (
    <div className="divide-y divide-slate-700/50">
      {pipelines.map((p: Pipeline) => (
        <button
          key={p.id}
          onClick={() => {
            setSelectedPipelineId(p.id);
            setView("detail");
          }}
          className={`w-full text-left px-4 py-3 transition-colors ${
            selectedPipelineId === p.id
              ? "bg-primary-500/10 border-l-2 border-primary-500"
              : "hover:bg-slate-700/30 border-l-2 border-transparent"
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-white font-medium truncate">{p.name}</span>
            <span className={`px-2 py-0.5 text-xs rounded-full ${STATUS_COLORS[p.status] || "bg-slate-500/20 text-slate-400"}`}>
              {p.status}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span>{p.total_nodes} nodes</span>
            <span>{p.completed_nodes}/{p.total_nodes} done</span>
            <span>{formatMs(p.execution_time_ms)}</span>
          </div>
          {/* Progress bar */}
          <div className="mt-2 w-full bg-slate-700 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all ${
                p.status === "failed" ? "bg-red-500" : p.status === "completed" ? "bg-green-500" : "bg-primary-500"
              }`}
              style={{ width: `${p.progress}%` }}
            />
          </div>
        </button>
      ))}
    </div>
  );
}
