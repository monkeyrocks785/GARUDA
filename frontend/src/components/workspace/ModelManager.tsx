import { useState } from "react";
import {
  useModelList,
  useRegisterModel,
  useLoadModel,
  useUnloadModel,
  useDeleteModel,
  useToggleModelFavorite,
} from "../../hooks/useIntelligence";
import type { ModelRegisterRequest } from "../../types/intelligence";

interface ModelManagerProps {
  projectId: string | undefined;
}

export default function ModelManager({ projectId: _projectId }: ModelManagerProps) {
  const [showRegister, setShowRegister] = useState(false);
  const [filter, setFilter] = useState<string>("");

  const { data: models = [], isLoading } = useModelList();
  const registerModel = useRegisterModel();
  const loadModel = useLoadModel();
  const unloadModel = useUnloadModel();
  const deleteModel = useDeleteModel();
  const toggleFavorite = useToggleModelFavorite();

  const [form, setForm] = useState<ModelRegisterRequest>({
    name: "",
    task: "detection",
    framework: "pytorch",
  });

  const filtered = models.filter(
    (m) =>
      !filter ||
      m.name.toLowerCase().includes(filter.toLowerCase()) ||
      m.task.includes(filter)
  );

  const handleRegister = () => {
    if (!form.name) return;
    registerModel.mutate(form, {
      onSuccess: () => {
        setShowRegister(false);
        setForm({ name: "", task: "detection", framework: "pytorch" });
      },
    });
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "ready": return "text-emerald-400 bg-emerald-900/30";
      case "loading": return "text-yellow-400 bg-yellow-900/30";
      case "error": return "text-red-400 bg-red-900/30";
      default: return "text-slate-400 bg-slate-700/50";
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-800">
      <div className="p-3 border-b border-slate-700 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">Model Registry</h3>
        <div className="flex gap-1">
          <input
            type="text"
            placeholder="Filter..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-24 px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300"
          />
          <button
            onClick={() => setShowRegister(!showRegister)}
            className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded"
          >
            + Register
          </button>
        </div>
      </div>

      {showRegister && (
        <div className="p-3 border-b border-slate-700 bg-slate-750 space-y-2">
          <input
            type="text"
            placeholder="Model name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300"
          />
          <div className="flex gap-2">
            <select
              value={form.task}
              onChange={(e) => setForm({ ...form, task: e.target.value })}
              className="flex-1 px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300"
            >
              <option value="detection">Detection</option>
              <option value="segmentation">Segmentation</option>
              <option value="classification">Classification</option>
              <option value="feature_extraction">Feature Extraction</option>
              <option value="similarity_search">Similarity Search</option>
            </select>
            <select
              value={form.framework}
              onChange={(e) => setForm({ ...form, framework: e.target.value })}
              className="flex-1 px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300"
            >
              <option value="pytorch">PyTorch</option>
              <option value="onnx">ONNX</option>
              <option value="tensorflow">TensorFlow</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div className="flex gap-1">
            <button
              onClick={handleRegister}
              disabled={!form.name}
              className="px-2 py-1 text-xs bg-emerald-600 hover:bg-emerald-500 text-white rounded disabled:opacity-50"
            >
              Register
            </button>
            <button
              onClick={() => setShowRegister(false)}
              className="px-2 py-1 text-xs bg-slate-600 hover:bg-slate-500 text-white rounded"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-slate-500 text-sm">Loading models...</div>
        ) : filtered.length === 0 ? (
          <div className="p-4 text-center text-slate-500 text-sm">
            {models.length === 0
              ? "No models registered. Click '+ Register' to add one."
              : "No models match filter."}
          </div>
        ) : (
          filtered.map((model) => (
            <div
              key={model.id}
              className="border-b border-slate-700 p-3 hover:bg-slate-750"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-200 truncate">
                      {model.name}
                    </span>
                    <span className="text-[10px] text-slate-500">v{model.version}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${statusColor(model.status)}`}>
                      {model.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    {model.task} | {model.framework} | {model.inference_count} runs
                  </div>
                  {model.description && (
                    <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                      {model.description}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex gap-1 mt-2">
                {model.is_loaded ? (
                  <button
                    onClick={() => unloadModel.mutate(model.id)}
                    className="px-2 py-0.5 text-[10px] bg-yellow-700 hover:bg-yellow-600 text-white rounded"
                  >
                    Unload
                  </button>
                ) : (
                  <button
                    onClick={() => loadModel.mutate(model.id)}
                    className="px-2 py-0.5 text-[10px] bg-emerald-700 hover:bg-emerald-600 text-white rounded"
                  >
                    Load
                  </button>
                )}
                <button
                  onClick={() => toggleFavorite.mutate(model.id)}
                  className="px-2 py-0.5 text-[10px] bg-slate-600 hover:bg-slate-500 text-white rounded"
                >
                  {model.favorite ? "★" : "☆"}
                </button>
                <button
                  onClick={() => {
                    if (confirm("Delete this model?")) deleteModel.mutate(model.id);
                  }}
                  className="px-2 py-0.5 text-[10px] bg-red-700 hover:bg-red-600 text-white rounded"
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
