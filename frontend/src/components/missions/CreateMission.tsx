import { useState } from "react";
import { useCreateMission } from "../../hooks/useMissions";
import { useMissionStore } from "../../store/useMissionStore";
import type { MissionStatus, MissionPriority } from "../../types/mission";
import { useToastStore } from "../../store/useToastStore";
import { getErrorMessage } from "../../utils/errorMessage";

const STATUSES: MissionStatus[] = ["support", "planning", "active", "paused", "completed", "archived", "cancelled"];
const PRIORITIES: MissionPriority[] = ["low", "medium", "high", "critical"];

export default function CreateMission() {
  const createMutation = useCreateMission();
  const { setView, setSelectedMissionId } = useMissionStore();
  const toast = useToastStore.getState();
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<MissionStatus>("planning");
  const [priority, setPriority] = useState<MissionPriority>("medium");

  const handleCreate = () => {
    if (!name.trim()) return;
    createMutation.mutate(
      { name, code: code || undefined, description: description || undefined, status, priority },
      {
        onSuccess: (mission) => {
          toast.success("Mission created");
          setSelectedMissionId(mission.id);
          setView("detail");
          setShowForm(false);
          setName("");
          setCode("");
          setDescription("");
        },
        onError: (err) => toast.error(getErrorMessage(err)),
      }
    );
  };

  return (
    <div className="p-3">
      <button
        onClick={() => setShowForm(!showForm)}
        className="w-full px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm rounded-lg transition-colors"
      >
        {showForm ? "Cancel" : "New Mission"}
      </button>

      {showForm && (
        <div className="mt-3 space-y-3">
          <input
            type="text"
            placeholder="Mission name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
          />
          <input
            type="text"
            placeholder="Code (optional)"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
          />
          <div className="flex gap-2">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as MissionStatus)}
              className="flex-1 bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as MissionPriority)}
              className="flex-1 bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-1.5 text-sm text-white"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleCreate}
            disabled={!name.trim() || createMutation.isPending}
            className="w-full px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm rounded-lg disabled:opacity-50"
          >
            {createMutation.isPending ? "Creating..." : "Create Mission"}
          </button>
        </div>
      )}
    </div>
  );
}
