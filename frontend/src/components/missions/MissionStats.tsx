import { useMissionStats } from "../../hooks/useMissions";

export default function MissionStats() {
  const { data: stats, isLoading, isError } = useMissionStats();

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
            <span className="text-slate-400">Planning</span>
            <span className="text-yellow-400">{stats.planning}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Active</span>
            <span className="text-green-400">{stats.active}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Completed</span>
            <span className="text-emerald-400">{stats.completed}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Paused</span>
            <span className="text-orange-400">{stats.paused}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Archived</span>
            <span className="text-slate-400">{stats.archived}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Cancelled</span>
            <span className="text-red-400">{stats.cancelled}</span>
          </div>
          <div className="pt-2 border-t border-slate-700/50 flex justify-between">
            <span className="text-slate-400">Projects</span>
            <span className="text-white">{stats.total_projects}</span>
          </div>
        </div>
      )}
    </div>
  );
}
