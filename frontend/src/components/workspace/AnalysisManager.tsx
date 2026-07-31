import { useState } from "react";
import {
  useModelList,
  useAnalysisJobList,
  useCreateAnalysisJob,
  useRunAnalysisJob,
  useCancelAnalysisJob,
  useDeleteAnalysisJob,
} from "../../hooks/useIntelligence";
import type { AnalysisJobCreateRequest } from "../../types/intelligence";

interface AnalysisManagerProps {
  projectId: string | undefined;
}

export default function AnalysisManager({ projectId }: AnalysisManagerProps) {
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<AnalysisJobCreateRequest>({
    name: "",
    model_id: "",
    input_path: "",
    task_type: "detection",
    confidence_threshold: 0.5,
    iou_threshold: 0.45,
    device: "cpu",
  });

  const { data: models = [] } = useModelList({ loaded_only: true });
  const { data: jobs = [], isLoading } = useAnalysisJobList(projectId || null);
  const createJob = useCreateAnalysisJob();
  const runJob = useRunAnalysisJob();
  const cancelJob = useCancelAnalysisJob();
  const deleteJob = useDeleteAnalysisJob();

  const handleCreate = () => {
    if (!projectId || !form.name || !form.model_id || !form.input_path) return;
    createJob.mutate(
      { projectId, data: form },
      {
        onSuccess: () => {
          setShowCreate(false);
          setForm({
            name: "",
            model_id: "",
            input_path: "",
            task_type: "detection",
            confidence_threshold: 0.5,
            iou_threshold: 0.45,
            device: "cpu",
          });
        },
      }
    );
  };

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: "bg-slate-600 text-slate-300",
      running: "bg-blue-700 text-blue-200",
      completed: "bg-emerald-700 text-emerald-200",
      failed: "bg-red-700 text-red-200",
      cancelled: "bg-yellow-700 text-yellow-200",
    };
    return colors[status] || "bg-slate-600 text-slate-300";
  };

  return (
    <div className="flex flex-col h-full bg-slate-800">
      <div className="p-3 border-b border-slate-700 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">Analysis Jobs</h3>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded"
        >
          + New Job
        </button>
      </div>

      {showCreate && (
        <div className="p-3 border-b border-slate-700 space-y-2">
          <input
            type="text"
            placeholder="Job name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300"
          />
          <select
            value={form.model_id}
            onChange={(e) => setForm({ ...form, model_id: e.target.value })}
            className="w-full px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300"
          >
            <option value="">Select model...</option>
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} v{m.version} ({m.task})
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Input path (folder or file)"
            value={form.input_path}
            onChange={(e) => setForm({ ...form, input_path: e.target.value })}
            className="w-full px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300"
          />
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="text-[10px] text-slate-500">Confidence</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={form.confidence_threshold}
                onChange={(e) =>
                  setForm({ ...form, confidence_threshold: parseFloat(e.target.value) })
                }
                className="w-full px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300"
              />
            </div>
            <div className="flex-1">
              <label className="text-[10px] text-slate-500">IoU</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={form.iou_threshold}
                onChange={(e) =>
                  setForm({ ...form, iou_threshold: parseFloat(e.target.value) })
                }
                className="w-full px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300"
              />
            </div>
            <div className="flex-1">
              <label className="text-[10px] text-slate-500">Device</label>
              <select
                value={form.device}
                onChange={(e) => setForm({ ...form, device: e.target.value })}
                className="w-full px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300"
              >
                <option value="cpu">CPU</option>
                <option value="cuda">CUDA</option>
                <option value="mps">MPS</option>
              </select>
            </div>
          </div>
          <div className="flex gap-1">
            <button
              onClick={handleCreate}
              disabled={!form.name || !form.model_id || !form.input_path}
              className="px-2 py-1 text-xs bg-emerald-600 hover:bg-emerald-500 text-white rounded disabled:opacity-50"
            >
              Create & Run
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-2 py-1 text-xs bg-slate-600 hover:bg-slate-500 text-white rounded"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-slate-500 text-sm">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="p-4 text-center text-slate-500 text-sm">No analysis jobs yet.</div>
        ) : (
          jobs.map((job) => (
            <div key={job.id} className="border-b border-slate-700 p-3">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-200 truncate">
                      {job.name}
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${statusBadge(job.status)}`}>
                      {job.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    {job.detection_count} detections | {job.execution_time_ms}ms
                    {job.progress > 0 && job.progress < 100 && (
                      <span className="ml-2">
                        {Math.round(job.progress)}%
                      </span>
                    )}
                  </div>
                  {job.status === "running" && (
                    <div className="mt-1 h-1 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 transition-all"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                  )}
                  {job.error_message && (
                    <div className="text-[10px] text-red-400 mt-1 truncate">
                      {job.error_message}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex gap-1 mt-2">
                {(job.status === "pending" || job.status === "failed") && (
                  <button
                    onClick={() => runJob.mutate(job.id)}
                    className="px-2 py-0.5 text-[10px] bg-emerald-700 hover:bg-emerald-600 text-white rounded"
                  >
                    Run
                  </button>
                )}
                {job.status === "running" && (
                  <button
                    onClick={() => cancelJob.mutate(job.id)}
                    className="px-2 py-0.5 text-[10px] bg-yellow-700 hover:bg-yellow-600 text-white rounded"
                  >
                    Cancel
                  </button>
                )}
                {job.status !== "running" && (
                  <button
                    onClick={() => {
                      if (confirm("Delete this job?"))
                        deleteJob.mutate({ jobId: job.id, projectId: job.project_id });
                    }}
                    className="px-2 py-0.5 text-[10px] bg-red-700 hover:bg-red-600 text-white rounded"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
