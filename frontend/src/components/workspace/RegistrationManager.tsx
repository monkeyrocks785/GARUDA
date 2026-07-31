import { useState } from "react";
import type { ImageRegistration, RegistrationCreateRequest } from "../../types/registration";
import {
  useRegistrationList,
  useCreateRegistration,
  useRunRegistration,
  useDeleteRegistration,
  useToggleFavorite,
} from "../../hooks/useRegistration";

interface RegistrationManagerProps {
  projectId: string;
  onSelectRegistration: (reg: ImageRegistration) => void;
  selectedRegistrationId: string | null;
}

export function RegistrationManager({
  projectId,
  onSelectRegistration,
  selectedRegistrationId,
}: RegistrationManagerProps) {
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState<RegistrationCreateRequest>({
    name: "",
    reference_path: "",
    target_path: "",
    mode: "automatic",
    feature_detector: "orb",
    transform_type: "affine",
    resampling: "bilinear",
  });

  const { data: registrations = [], isLoading } = useRegistrationList(projectId);
  const createMutation = useCreateRegistration();
  const runMutation = useRunRegistration();
  const deleteMutation = useDeleteRegistration();
  const favMutation = useToggleFavorite();

  const handleCreate = () => {
    if (!formData.name || !formData.reference_path || !formData.target_path) return;
    createMutation.mutate(
      { projectId, data: formData },
      {
        onSuccess: (reg) => {
          setShowCreate(false);
          setFormData({
            name: "",
            reference_path: "",
            target_path: "",
            mode: "automatic",
            feature_detector: "orb",
            transform_type: "affine",
            resampling: "bilinear",
          });
          onSelectRegistration(reg);
        },
      }
    );
  };

  const handleRun = (e: React.MouseEvent, regId: string) => {
    e.stopPropagation();
    runMutation.mutate(regId);
  };

  const handleDelete = (e: React.MouseEvent, regId: string) => {
    e.stopPropagation();
    if (confirm("Delete this registration?")) {
      deleteMutation.mutate({ registrationId: regId, projectId });
    }
  };

  const handleFavorite = (e: React.MouseEvent, regId: string) => {
    e.stopPropagation();
    favMutation.mutate(regId);
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-green-400";
      case "running":
        return "text-blue-400";
      case "failed":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-800 text-white">
      <div className="flex items-center justify-between p-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200">Image Registration</h3>
        <div className="flex gap-1">
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-500 rounded"
          >
            {showCreate ? "Cancel" : "+ New"}
          </button>
        </div>
      </div>

      {showCreate && (
        <div className="p-3 border-b border-gray-700 space-y-2">
          <input
            type="text"
            placeholder="Registration name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
          />
          <input
            type="text"
            placeholder="Reference image path"
            value={formData.reference_path}
            onChange={(e) =>
              setFormData({ ...formData, reference_path: e.target.value })
            }
            className="w-full px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
          />
          <input
            type="text"
            placeholder="Target image path"
            value={formData.target_path}
            onChange={(e) =>
              setFormData({ ...formData, target_path: e.target.value })
            }
            className="w-full px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
          />
          <div className="grid grid-cols-2 gap-2">
            <select
              value={formData.mode}
              onChange={(e) => setFormData({ ...formData, mode: e.target.value })}
              className="px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
            >
              <option value="automatic">Automatic</option>
              <option value="manual">Manual</option>
            </select>
            <select
              value={formData.feature_detector}
              onChange={(e) =>
                setFormData({ ...formData, feature_detector: e.target.value })
              }
              className="px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
            >
              <option value="orb">ORB</option>
              <option value="akaze">AKAZE</option>
              <option value="brisk">BRISK</option>
              <option value="sift">SIFT</option>
            </select>
            <select
              value={formData.transform_type}
              onChange={(e) =>
                setFormData({ ...formData, transform_type: e.target.value })
              }
              className="px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
            >
              <option value="affine">Affine</option>
              <option value="perspective">Perspective</option>
              <option value="translation">Translation</option>
              <option value="rotation">Rotation</option>
            </select>
            <select
              value={formData.resampling}
              onChange={(e) =>
                setFormData({ ...formData, resampling: e.target.value })
              }
              className="px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
            >
              <option value="bilinear">Bilinear</option>
              <option value="nearest">Nearest</option>
              <option value="cubic">Cubic</option>
            </select>
          </div>
          <button
            onClick={handleCreate}
            disabled={createMutation.isPending}
            className="w-full px-2 py-1 text-xs bg-green-600 hover:bg-green-500 rounded disabled:opacity-50"
          >
            {createMutation.isPending ? "Creating..." : "Create Registration"}
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-400 text-xs">Loading...</div>
        ) : registrations.length === 0 ? (
          <div className="p-4 text-center text-gray-400 text-xs">
            No registrations yet. Click "+ New" to create one.
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {registrations.map((reg) => (
              <div
                key={reg.id}
                onClick={() => onSelectRegistration(reg)}
                className={`p-3 cursor-pointer hover:bg-gray-700 ${
                  selectedRegistrationId === reg.id ? "bg-gray-700" : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-gray-200 truncate">
                        {reg.name}
                      </span>
                      <span className={`text-xs ${statusColor(reg.status)}`}>
                        {reg.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1 truncate">
                      {reg.mode} • {reg.feature_detector} • {reg.transform_type}
                    </p>
                    {reg.confidence_score !== null && (
                      <p className="text-xs text-gray-400 mt-1">
                        Score: {reg.confidence_score.toFixed(1)} • RMSE:{" "}
                        {reg.rmse?.toFixed(2)}px
                      </p>
                    )}
                  </div>
                  <div className="flex gap-1 ml-2">
                    <button
                      onClick={(e) => handleFavorite(e, reg.id)}
                      className="text-xs text-gray-400 hover:text-yellow-400"
                      title="Toggle favorite"
                    >
                      {reg.favorite ? "★" : "☆"}
                    </button>
                    {reg.status === "pending" && (
                      <button
                        onClick={(e) => handleRun(e, reg.id)}
                        disabled={runMutation.isPending}
                        className="text-xs text-blue-400 hover:text-blue-300"
                        title="Run registration"
                      >
                        ▶
                      </button>
                    )}
                    <button
                      onClick={(e) => handleDelete(e, reg.id)}
                      className="text-xs text-gray-400 hover:text-red-400"
                      title="Delete"
                    >
                      ×
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
