import {
  useAnalysisJob,
  useJobReviewStats,
  useJobDetections,
} from "../../hooks/useIntelligence";

interface ResultsPanelProps {
  jobId: string | null;
}

export default function ResultsPanel({ jobId }: ResultsPanelProps) {
  const { data: job } = useAnalysisJob(jobId);
  const { data: stats } = useJobReviewStats(jobId);
  const { data: detections = [] } = useJobDetections(jobId);

  if (!jobId || !job) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 text-sm">
        Select a job to view results
      </div>
    );
  }

  const classCounts: Record<string, number> = {};
  detections.forEach((d) => {
    classCounts[d.class_name] = (classCounts[d.class_name] || 0) + 1;
  });

  const statusColor = (status: string) => {
    switch (status) {
      case "completed": return "text-emerald-400";
      case "running": return "text-blue-400";
      case "failed": return "text-red-400";
      case "pending": return "text-yellow-400";
      default: return "text-slate-400";
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-800 p-4 space-y-4 overflow-y-auto">
      <h3 className="text-sm font-semibold text-slate-200">Job Results</h3>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-750 rounded p-3 border border-slate-700">
          <div className="text-[10px] text-slate-500 uppercase">Status</div>
          <div className={`text-sm font-medium ${statusColor(job.status)}`}>{job.status}</div>
        </div>
        <div className="bg-slate-750 rounded p-3 border border-slate-700">
          <div className="text-[10px] text-slate-500 uppercase">Detections</div>
          <div className="text-sm font-medium text-slate-200">{job.detection_count}</div>
        </div>
        <div className="bg-slate-750 rounded p-3 border border-slate-700">
          <div className="text-[10px] text-slate-500 uppercase">Time</div>
          <div className="text-sm font-medium text-slate-200">{job.execution_time_ms}ms</div>
        </div>
        <div className="bg-slate-750 rounded p-3 border border-slate-700">
          <div className="text-[10px] text-slate-500 uppercase">Progress</div>
          <div className="text-sm font-medium text-slate-200">{Math.round(job.progress)}%</div>
        </div>
      </div>

      {job.status === "running" && (
        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      )}

      {stats && (
        <div className="bg-slate-750 rounded p-3 border border-slate-700">
          <div className="text-[10px] text-slate-500 uppercase mb-2">Review Stats</div>
          <div className="grid grid-cols-4 gap-2 text-center">
            <div>
              <div className="text-lg font-bold text-slate-300">{stats.pending}</div>
              <div className="text-[10px] text-slate-500">Pending</div>
            </div>
            <div>
              <div className="text-lg font-bold text-emerald-400">{stats.accepted}</div>
              <div className="text-[10px] text-slate-500">Accepted</div>
            </div>
            <div>
              <div className="text-lg font-bold text-red-400">{stats.rejected}</div>
              <div className="text-[10px] text-slate-500">Rejected</div>
            </div>
            <div>
              <div className="text-lg font-bold text-yellow-400">{stats.uncertain}</div>
              <div className="text-[10px] text-slate-500">Uncertain</div>
            </div>
          </div>
        </div>
      )}

      {Object.keys(classCounts).length > 0 && (
        <div className="bg-slate-750 rounded p-3 border border-slate-700">
          <div className="text-[10px] text-slate-500 uppercase mb-2">By Class</div>
          {Object.entries(classCounts).map(([cls, count]) => (
            <div key={cls} className="flex items-center justify-between py-1">
              <span className="text-xs text-slate-300">{cls}</span>
              <span className="text-xs text-slate-400">{count}</span>
            </div>
          ))}
        </div>
      )}

      {job.error_message && (
        <div className="bg-red-900/30 rounded p-3 border border-red-800">
          <div className="text-[10px] text-red-400 uppercase mb-1">Error</div>
          <div className="text-xs text-red-300">{job.error_message}</div>
        </div>
      )}
    </div>
  );
}
