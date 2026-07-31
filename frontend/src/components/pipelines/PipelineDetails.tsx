import { useState } from "react";
import { usePipeline, usePipelineNodes, usePipelineHistory, usePipelineLogs, useStartPipeline, usePausePipeline, useResumePipeline, useCancelPipeline, useRetryPipeline, useDeletePipeline } from "../../hooks/usePipelines";
import { usePipelineStore } from "../../store/usePipelineStore";
import type { PipelineNode, PipelineHistory, PipelineLog } from "../../types/pipeline";
import { STATUS_COLORS, NODE_TYPE_ICONS } from "../../types/pipeline";
import { getErrorMessage } from "../../utils/errorMessage";
import { useToastStore } from "../../store/useToastStore";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";
import EmptyState from "../ui/EmptyState";
import ConfirmDialog from "../ui/ConfirmDialog";

function formatMs(ms: number): string {
  if (ms === 0) return "-";
  if (ms < 1000) return `${ms}ms`;
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)}s`;
  return `${(s / 60).toFixed(1)}m`;
}

export default function PipelineDetails() {
  const { selectedPipelineId } = usePipelineStore();
  const { data: pipeline, isLoading, isError, error, refetch } = usePipeline(selectedPipelineId);
  const { data: nodes } = usePipelineNodes(selectedPipelineId);
  const { data: history } = usePipelineHistory(selectedPipelineId);
  const { data: logs } = usePipelineLogs(selectedPipelineId);
  const startMutation = useStartPipeline();
  const pauseMutation = usePausePipeline();
  const resumeMutation = useResumePipeline();
  const cancelMutation = useCancelPipeline();
  const retryMutation = useRetryPipeline();
  const deleteMutation = useDeletePipeline();
  const toast = useToastStore.getState();
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  const runMutation = (m: { mutate: (id: string, opts?: any) => void }, id: string, success: string) => {
    m.mutate(id, {
      onSuccess: () => toast.success(success),
      onError: (err: unknown) => toast.error(getErrorMessage(err)),
    });
  };

  if (!selectedPipelineId) {
    return (
      <EmptyState
        compact
        title="No pipeline selected"
        description="Select a pipeline to view details"
      />
    );
  }

  if (isLoading) {
    return <LoadingState compact label="Loading pipeline..." />;
  }

  if (isError) {
    return (
      <ErrorState
        compact
        title="Failed to load pipeline"
        message={getErrorMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  if (!pipeline) {
    return (
      <EmptyState
        compact
        title="No pipeline selected"
        description="Select a pipeline to view details"
      />
    );
  }

  const formatDate = (s: string | null) => {
    if (!s) return "-";
    return new Date(s).toLocaleString();
  };

  return (
    <div className="p-4 space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-white">{pipeline.name}</h2>
          <span className={`px-2 py-1 text-xs rounded-full ${STATUS_COLORS[pipeline.status]}`}>
            {pipeline.status}
          </span>
        </div>
        {pipeline.description && (
          <p className="text-sm text-slate-400">{pipeline.description}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        {(pipeline.status === "pending" || pipeline.status === "queued") && (
          <button onClick={() => runMutation(startMutation, pipeline.id, "Pipeline started")} className="px-3 py-1.5 text-sm rounded-lg bg-green-600 hover:bg-green-700 text-white">
            Start
          </button>
        )}
        {pipeline.status === "running" && (
          <>
            <button onClick={() => runMutation(pauseMutation, pipeline.id, "Pipeline paused")} className="px-3 py-1.5 text-sm rounded-lg bg-yellow-600 hover:bg-yellow-700 text-white">
              Pause
            </button>
            <button onClick={() => runMutation(cancelMutation, pipeline.id, "Pipeline cancelled")} className="px-3 py-1.5 text-sm rounded-lg bg-red-600 hover:bg-red-700 text-white">
              Cancel
            </button>
          </>
        )}
        {pipeline.status === "paused" && (
          <button onClick={() => runMutation(resumeMutation, pipeline.id, "Pipeline resumed")} className="px-3 py-1.5 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white">
            Resume
          </button>
        )}
        {pipeline.status === "failed" && (
          <button onClick={() => runMutation(retryMutation, pipeline.id, "Pipeline retry scheduled")} className="px-3 py-1.5 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white">
            Retry
          </button>
        )}
        <button onClick={() => setConfirmDeleteOpen(true)} className="px-3 py-1.5 text-sm rounded-lg bg-slate-700 hover:bg-slate-600 text-white">
          Delete
        </button>
      </div>
      <ConfirmDialog
        open={confirmDeleteOpen}
        title="Delete pipeline"
        message={`Delete pipeline "${pipeline.name}"? This cannot be undone.`}
        confirmLabel="Delete"
        danger
        onCancel={() => setConfirmDeleteOpen(false)}
        onConfirm={() => {
          deleteMutation.mutate(pipeline.id, {
            onSuccess: () => {
              toast.success("Pipeline deleted");
              setConfirmDeleteOpen(false);
            },
            onError: (err) => {
              toast.error(getErrorMessage(err));
              setConfirmDeleteOpen(false);
            },
          });
        }}
      />

      {/* Progress */}
      <div className="bg-slate-800/50 rounded-xl p-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-slate-400">Progress</span>
          <span className="text-white">{pipeline.completed_nodes}/{pipeline.total_nodes} nodes ({Math.round(pipeline.progress)}%)</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${pipeline.status === "failed" ? "bg-red-500" : pipeline.status === "completed" ? "bg-green-500" : "bg-primary-500"}`}
            style={{ width: `${pipeline.progress}%` }}
          />
        </div>
      </div>

      {/* Node Graph Visualization */}
      {nodes && nodes.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Pipeline Flow</h3>
          <div className="flex flex-col items-center gap-2">
            {nodes.map((node: PipelineNode, i: number) => (
              <div key={node.id} className="flex flex-col items-center">
                <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${
                  node.status === "completed" ? "border-green-500 bg-green-500/10" :
                  node.status === "running" ? "border-blue-500 bg-blue-500/10 animate-pulse" :
                  node.status === "failed" ? "border-red-500 bg-red-500/10" :
                  "border-slate-600 bg-slate-700/50"
                }`}>
                  <span className="w-6 h-6 rounded bg-primary-600 flex items-center justify-center text-[10px] font-bold text-white">
                    {NODE_TYPE_ICONS[node.node_type] || "?"}
                  </span>
                  <div>
                    <p className="text-sm text-white">{node.name}</p>
                    <p className="text-xs text-slate-500">{node.node_type} · {formatMs(node.execution_time_ms)}</p>
                  </div>
                  <span className={`ml-2 w-2 h-2 rounded-full ${
                    node.status === "completed" ? "bg-green-500" :
                    node.status === "running" ? "bg-blue-500" :
                    node.status === "failed" ? "bg-red-500" :
                    "bg-slate-500"
                  }`} />
                </div>
                {i < nodes.length - 1 && (
                  <div className="w-0.5 h-4 bg-slate-600" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Properties */}
      <div className="bg-slate-800/50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3">Properties</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">Started</span>
            <span className="text-white">{formatDate(pipeline.started_at)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Completed</span>
            <span className="text-white">{formatDate(pipeline.completed_at)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Execution Time</span>
            <span className="text-white">{formatMs(pipeline.execution_time_ms)}</span>
          </div>
          {pipeline.error_message && (
            <div className="flex justify-between">
              <span className="text-slate-400">Error</span>
              <span className="text-red-400 text-xs">{pipeline.error_message}</span>
            </div>
          )}
        </div>
      </div>

      {/* History */}
      {history && history.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">History</h3>
          <div className="space-y-2">
            {history.slice(0, 10).map((h: PipelineHistory) => (
              <div key={h.id} className="flex items-start gap-3 text-sm">
                <span className="text-xs text-slate-500 shrink-0">{formatDate(h.timestamp)}</span>
                <span className={`px-2 py-0.5 text-xs rounded ${
                  h.action === "completed" ? "bg-green-500/20 text-green-400" :
                  h.action === "failed" ? "bg-red-500/20 text-red-400" :
                  "bg-slate-500/20 text-slate-400"
                }`}>{h.action}</span>
                {h.details && <span className="text-slate-400">{h.details}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logs */}
      {logs && logs.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Logs</h3>
          <div className="space-y-1 font-mono text-xs">
            {logs.slice(0, 20).map((l: PipelineLog) => (
              <div key={l.id} className={`flex gap-2 ${
                l.level === "error" ? "text-red-400" :
                l.level === "warning" ? "text-yellow-400" :
                "text-slate-400"
              }`}>
                <span className="text-slate-600">{formatDate(l.timestamp)}</span>
                <span className="uppercase w-12">{l.level}</span>
                <span>{l.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
