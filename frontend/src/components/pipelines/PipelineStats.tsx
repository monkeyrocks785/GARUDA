import { usePipelineStats, useQueueStatus } from "../../hooks/usePipelines";

export default function PipelineStats() {
  const { data: stats, isLoading, isError } = usePipelineStats();
  const { data: queue } = useQueueStatus();

  return (
    <div className="p-3 space-y-3">
      <span className="text-xs font-semibold text-slate-400 uppercase">Stats</span>
      {isLoading && (
        <div className="text-xs text-slate-500 text-center py-2">Loading stats...</div>
      )}
      {isError && (
        <div className="text-xs text-red-400 text-center py-2">Failed to load stats</div>
      )}
      {!isLoading && !isError && stats && (
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">Total</span>
            <span className="text-white">{stats.total}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Running</span>
            <span className="text-blue-400">{stats.running}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Completed</span>
            <span className="text-green-400">{stats.completed}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Failed</span>
            <span className="text-red-400">{stats.failed}</span>
          </div>
        </div>
      )}
      {queue && (
        <div className="pt-2 border-t border-slate-700/50 space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">In Queue</span>
            <span className="text-white">{queue.total}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Waiting</span>
            <span className="text-blue-400">{queue.waiting}</span>
          </div>
        </div>
      )}
    </div>
  );
}
