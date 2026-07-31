import { useState } from "react";
import { useMission, useDeleteMission, useArchiveMission, useToggleFavorite, useMissionTimeline, useMissionNotes, useMissionProjects } from "../../hooks/useMissions";
import { useMissionStore } from "../../store/useMissionStore";
import type { MissionActivity, MissionNote } from "../../types/mission";
import { STATUS_COLORS, PRIORITY_COLORS } from "../../types/mission";
import { parseTagArray } from "../../utils/json";
import { getErrorMessage } from "../../utils/errorMessage";
import { useToastStore } from "../../store/useToastStore";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";
import EmptyState from "../ui/EmptyState";
import ConfirmDialog from "../ui/ConfirmDialog";

export default function MissionDetails() {
  const { selectedMissionId } = useMissionStore();
  const { data: mission, isLoading, isError, error, refetch } = useMission(selectedMissionId);
  const { data: timeline } = useMissionTimeline(selectedMissionId);
  const { data: notes } = useMissionNotes(selectedMissionId);
  const { data: projects } = useMissionProjects(selectedMissionId);
  const deleteMutation = useDeleteMission();
  const archiveMutation = useArchiveMission();
  const favMutation = useToggleFavorite();
  const toast = useToastStore.getState();
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  if (!selectedMissionId) {
    return (
      <EmptyState
        compact
        title="No mission selected"
        description="Select a mission to view details"
      />
    );
  }

  if (isLoading) {
    return <LoadingState compact label="Loading mission..." />;
  }

  if (isError) {
    return (
      <ErrorState
        compact
        title="Failed to load mission"
        message={getErrorMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  if (!mission) {
    return (
      <EmptyState
        compact
        title="No mission selected"
        description="Select a mission to view details"
      />
    );
  }

  const formatDate = (s: string | null | undefined) => {
    if (!s) return "-";
    return new Date(s).toLocaleString();
  };

  return (
    <div className="p-4 space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white">{mission.name}</h2>
            {mission.code && <span className="text-xs text-slate-500">({mission.code})</span>}
          </div>
          <div className="flex gap-1">
            <span className={`px-2 py-1 text-xs rounded-full ${PRIORITY_COLORS[mission.priority]}`}>
              {mission.priority}
            </span>
            <span className={`px-2 py-1 text-xs rounded-full ${STATUS_COLORS[mission.status]}`}>
              {mission.status}
            </span>
          </div>
        </div>
        {mission.description && (
          <p className="text-sm text-slate-400">{mission.description}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() =>
            favMutation.mutate(mission.id, {
              onSuccess: () =>
                toast.success(mission.favorite ? "Removed from favorites" : "Added to favorites"),
              onError: (err) => toast.error(getErrorMessage(err)),
            })
          }
          className="px-3 py-1.5 text-sm rounded-lg bg-slate-700 hover:bg-slate-600 text-white"
        >
          {mission.favorite ? "Unfavorite" : "Favorite"}
        </button>
        <button
          onClick={() =>
            archiveMutation.mutate(mission.id, {
              onSuccess: () => toast.success("Mission archived"),
              onError: (err) => toast.error(getErrorMessage(err)),
            })
          }
          className="px-3 py-1.5 text-sm rounded-lg bg-slate-700 hover:bg-slate-600 text-white"
        >
          Archive
        </button>
        <button
          onClick={() => setConfirmDeleteOpen(true)}
          className="px-3 py-1.5 text-sm rounded-lg bg-red-600/20 hover:bg-red-600/40 text-red-400"
        >
          Delete
        </button>
      </div>
      <ConfirmDialog
        open={confirmDeleteOpen}
        title="Delete mission"
        message={`Delete mission "${mission.name}"? This cannot be undone.`}
        confirmLabel="Delete"
        danger
        onCancel={() => setConfirmDeleteOpen(false)}
        onConfirm={() => {
          deleteMutation.mutate(mission.id, {
            onSuccess: () => {
              toast.success("Mission deleted");
              setConfirmDeleteOpen(false);
            },
            onError: (err) => {
              toast.error(getErrorMessage(err));
              setConfirmDeleteOpen(false);
            },
          });
        }}
      />

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Projects", value: mission.project_count },
          { label: "Datasets", value: mission.dataset_count },
          { label: "Pipelines", value: mission.pipeline_count },
          { label: "Reports", value: mission.report_count },
        ].map((s) => (
          <div key={s.label} className="bg-slate-800/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-white">{s.value}</p>
            <p className="text-xs text-slate-500">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Properties */}
      <div className="bg-slate-800/50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3">Properties</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">Classification</span>
            <span className="text-white">{mission.classification || "-"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Created By</span>
            <span className="text-white">{mission.created_by || "-"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Start</span>
            <span className="text-white">{formatDate(mission.mission_start)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">End</span>
            <span className="text-white">{formatDate(mission.mission_end)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Created</span>
            <span className="text-white">{formatDate(mission.created_at)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Modified</span>
            <span className="text-white">{formatDate(mission.modified_at)}</span>
          </div>
        </div>
      </div>

      {/* Tags */}
      {mission.tags && (
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Tags</h3>
          <div className="flex flex-wrap gap-1">
            {parseTagArray(mission.tags).map((tag: string) => (
              <span key={tag} className="px-2 py-0.5 text-xs rounded bg-primary-500/20 text-primary-400">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Projects */}
      {projects && projects.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Linked Projects ({projects.length})</h3>
          <div className="space-y-2">
            {projects.map((p: any) => (
              <div key={p.project_id} className="flex items-center justify-between text-sm">
                <span className="text-white">{p.project_id.slice(0, 8)}...</span>
                <span className="text-xs text-slate-500">{formatDate(p.added_at)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timeline */}
      {timeline && timeline.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Timeline</h3>
          <div className="space-y-3">
            {timeline.slice(0, 10).map((a: MissionActivity) => (
              <div key={a.id} className="flex items-start gap-3 text-sm">
                <div className="w-2 h-2 rounded-full bg-primary-500 mt-1.5 shrink-0" />
                <div>
                  <p className="text-white">{a.action}</p>
                  {a.details && <p className="text-xs text-slate-500">{a.details}</p>}
                  <p className="text-xs text-slate-600">{formatDate(a.timestamp)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      {notes && notes.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Notes ({notes.length})</h3>
          <div className="space-y-3">
            {notes.map((n: MissionNote) => (
              <div key={n.id} className="border-l-2 border-slate-600 pl-3">
                {n.title && <p className="text-sm text-white font-medium">{n.title}</p>}
                {n.content && <p className="text-xs text-slate-400 mt-1">{n.content}</p>}
                <p className="text-xs text-slate-600 mt-1">{n.author || "Anonymous"} - {formatDate(n.created_at)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
