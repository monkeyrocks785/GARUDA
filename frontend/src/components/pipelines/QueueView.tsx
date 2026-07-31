import { useQueueStatus, useQueueEntries } from "../../hooks/usePipelines";
import type { QueueEntry } from "../../types/pipeline";
import { STATUS_COLORS } from "../../types/pipeline";
import { getErrorMessage } from "../../utils/errorMessage";
import ErrorState from "../ui/ErrorState";

export default function QueueView() {
  const { data: status } = useQueueStatus();
  const { data: entries, isLoading, isError, error, refetch } = useQueueEntries();

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold text-white">Processing Queue</h2>

      {/* Stats */}
      {status && (
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: "Waiting", value: status.waiting, color: "text-blue-400" },
            { label: "Running", value: status.running, color: "text-green-400" },
            { label: "Failed", value: status.failed, color: "text-red-400" },
            { label: "Total", value: status.total, color: "text-white" },
          ].map((s) => (
            <div key={s.label} className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-slate-500">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Queue List */}
      {isLoading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500"></div>
        </div>
      ) : isError ? (
        <ErrorState
          compact
          title="Failed to load queue"
          message={getErrorMessage(error)}
          onRetry={() => refetch()}
        />
      ) : !entries || entries.length === 0 ? (
        <div className="text-center py-8 text-slate-400">
          <p>Queue is empty</p>
        </div>
      ) : (
        <div className="space-y-2">
          {entries.map((e: QueueEntry) => (
            <div key={e.id} className="bg-slate-800/50 rounded-lg p-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm text-slate-400">#{e.position}</span>
                <span className="text-sm text-white">{e.pipeline_id.slice(0, 8)}...</span>
                {e.worker_id && (
                  <span className="text-xs text-slate-500">Worker: {e.worker_id}</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">P{e.priority}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full ${STATUS_COLORS[e.status]}`}>
                  {e.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
