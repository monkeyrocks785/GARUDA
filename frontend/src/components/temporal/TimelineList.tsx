import { useState } from "react";
import { useTimelines, useDeleteTimeline, useToggleFavorite, useDuplicateTimeline, useTimelineStats } from "../../hooks/useTemporal";
import { useTemporalStore } from "../../store/useTemporalStore";
import CreateTimeline from "./CreateTimeline";
import type { Timeline } from "../../types/temporal";
import { getErrorMessage } from "../../utils/errorMessage";
import { useToastStore } from "../../store/useToastStore";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";
import EmptyState from "../ui/EmptyState";

export default function TimelineList() {
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const { setSelectedTimelineId, setView } = useTemporalStore();

  const { data, isLoading, isError, error, refetch } = useTimelines({ search: search || undefined });
  const { data: stats } = useTimelineStats();
  const deleteTimeline = useDeleteTimeline();
  const toggleFav = useToggleFavorite();
  const duplicateTimeline = useDuplicateTimeline();
  const toast = useToastStore.getState();

  const timelines = data?.timelines || [];

  if (showCreate) {
    return <CreateTimeline onDone={() => setShowCreate(false)} />;
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Timelines</h2>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          + New Timeline
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-2xl font-bold text-white">{stats.total_timelines}</div>
            <div className="text-sm text-slate-400">Timelines</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
            <div className="text-2xl font-bold text-white">{stats.total_entries}</div>
            <div className="text-sm text-slate-400">Total Entries</div>
          </div>
        </div>
      )}

      <input
        type="text"
        placeholder="Search timelines..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white placeholder-slate-400"
      />

      {isLoading ? (
        <LoadingState compact label="Loading timelines..." />
      ) : isError ? (
        <ErrorState
          compact
          title="Failed to load timelines"
          message={getErrorMessage(error)}
          onRetry={() => refetch()}
        />
      ) : timelines.length === 0 ? (
        <EmptyState
          title="No timelines yet"
          description="Create a timeline to start tracking temporal data"
          action={
            <button onClick={() => setShowCreate(true)} className="btn-primary">
              + Create Timeline
            </button>
          }
        />
      ) : (
        <div className="space-y-2">
          {timelines.map((t: Timeline) => (
            <div
              key={t.id}
              className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 hover:border-primary-500/50 cursor-pointer transition-colors"
              onClick={() => {
                setSelectedTimelineId(t.id);
                setView("detail");
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <span className="text-purple-400 font-bold">T</span>
                  </div>
                  <div>
                    <h3 className="text-white font-medium">{t.name}</h3>
                    <p className="text-sm text-slate-400">
                      {t.entry_count} entries | {t.group_by} grouping
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFav.mutate(t.id, {
                        onSuccess: () =>
                          toast.success(t.favorite ? "Removed from favorites" : "Added to favorites"),
                        onError: (err) => toast.error(getErrorMessage(err)),
                      });
                    }}
                    className="p-1 hover:bg-slate-700/50 rounded"
                  >
                    {t.favorite ? "★" : "☆"}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      duplicateTimeline.mutate(
                        { id: t.id },
                        {
                          onSuccess: () => toast.success("Timeline duplicated"),
                          onError: (err) => toast.error(getErrorMessage(err)),
                        }
                      );
                    }}
                    className="p-1 hover:bg-slate-700/50 rounded text-slate-400"
                    title="Duplicate"
                  >
                    ⧉
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm("Delete this timeline?")) {
                        deleteTimeline.mutate(t.id, {
                          onSuccess: () => toast.success("Timeline deleted"),
                          onError: (err) => toast.error(getErrorMessage(err)),
                        });
                      }
                    }}
                    className="p-1 hover:bg-red-500/20 rounded text-slate-400 hover:text-red-400"
                    title="Delete"
                  >
                    ✕
                  </button>
                </div>
              </div>
              {t.description && (
                <p className="text-sm text-slate-400 mt-2 ml-13">{t.description}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
