import { useMissions } from "../../hooks/useMissions";
import { useMissionStore } from "../../store/useMissionStore";
import type { Mission } from "../../types/mission";
import { STATUS_COLORS, PRIORITY_COLORS } from "../../types/mission";
import { getErrorMessage } from "../../utils/errorMessage";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";
import EmptyState from "../ui/EmptyState";

export default function MissionList() {
  const { data, isLoading, isError, error, refetch } = useMissions();
  const { selectedMissionId, setSelectedMissionId, setView } = useMissionStore();

  if (isLoading) {
    return <LoadingState compact label="Loading missions..." />;
  }

  if (isError) {
    return (
      <ErrorState
        compact
        title="Failed to load missions"
        message={getErrorMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  const missions = data?.missions || [];

  if (missions.length === 0) {
    return (
      <EmptyState
        compact
        title="No missions yet"
        description="Create a mission to get started"
      />
    );
  }

  return (
    <div className="divide-y divide-slate-700/50">
      {missions.map((m: Mission) => (
        <button
          key={m.id}
          onClick={() => {
            setSelectedMissionId(m.id);
            setView("detail");
          }}
          className={`w-full text-left px-4 py-3 transition-colors ${
            selectedMissionId === m.id
              ? "bg-primary-500/10 border-l-2 border-primary-500"
              : "hover:bg-slate-700/30 border-l-2 border-transparent"
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-white font-medium truncate">{m.name}</span>
            <div className="flex gap-1">
              <span className={`px-2 py-0.5 text-xs rounded-full ${PRIORITY_COLORS[m.priority]}`}>
                {m.priority}
              </span>
              <span className={`px-2 py-0.5 text-xs rounded-full ${STATUS_COLORS[m.status]}`}>
                {m.status}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            {m.code && <span>{m.code}</span>}
            <span>{m.project_count} projects</span>
          </div>
        </button>
      ))}
    </div>
  );
}
