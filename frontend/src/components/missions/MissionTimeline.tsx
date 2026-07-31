import { useMissionTimeline } from "../../hooks/useMissions";
import { useMissionStore } from "../../store/useMissionStore";
import type { MissionActivity } from "../../types/mission";

export default function MissionTimeline() {
  const { selectedMissionId } = useMissionStore();
  const { data: timeline, isLoading } = useMissionTimeline(selectedMissionId);

  const formatDate = (s: string) => new Date(s).toLocaleString();

  if (!selectedMissionId) {
    return (
      <div className="text-center py-12 text-slate-400">
        <p>Select a mission to view timeline</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-semibold text-white">Mission Timeline</h2>
      {!timeline || timeline.length === 0 ? (
        <div className="text-center py-8 text-slate-400">
          <p>No activity yet</p>
        </div>
      ) : (
        <div className="relative">
          <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-slate-700" />
          <div className="space-y-4">
            {timeline.map((a: MissionActivity) => (
              <div key={a.id} className="flex items-start gap-4 pl-8 relative">
                <div className="absolute left-1.5 top-1 w-3 h-3 rounded-full bg-primary-500 border-2 border-slate-900" />
                <div className="flex-1 bg-slate-800/50 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-white font-medium">{a.action}</span>
                    <span className="text-xs text-slate-500">{formatDate(a.timestamp)}</span>
                  </div>
                  {a.details && <p className="text-xs text-slate-400">{a.details}</p>}
                  {a.entity_type && (
                    <span className="inline-block mt-1 px-2 py-0.5 text-[10px] rounded bg-slate-700 text-slate-400">
                      {a.entity_type}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
