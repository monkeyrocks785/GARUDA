import { useState } from "react";
import { useTimeline, useTimelineEntries, useTimelineSensors, useTimelineLogs, useDeleteTimeline, useUpdateTimeline, useRemoveEntry, useCreateComparison } from "../../hooks/useTemporal";
import { useTemporalStore } from "../../store/useTemporalStore";
import TimelinePlayer from "./TimelinePlayer";
import TimelineToolbar from "./TimelineToolbar";
import DateFilter from "./DateFilter";
import SensorFilter from "./SensorFilter";
import type { TimelineEntry } from "../../types/temporal";
import { getErrorMessage } from "../../utils/errorMessage";
import { useToastStore } from "../../store/useToastStore";
import LoadingState from "../ui/LoadingState";
import ErrorState from "../ui/ErrorState";

interface Props {
  timelineId: string;
}

export default function TimelineDetails({ timelineId }: Props) {
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [playerIndex, setPlayerIndex] = useState(0);

  const { setView, dateRange, setDateRange, sensorFilter, setSensorFilter, comparisonMode, setComparisonMode } = useTemporalStore();
  const { data: timeline, isLoading, isError, error, refetch } = useTimeline(timelineId);
  const { data: entries = [] } = useTimelineEntries(timelineId, {
    sensor: sensorFilter || undefined,
    date_from: dateRange.from || undefined,
    date_to: dateRange.to || undefined,
  });
  const { data: sensorData } = useTimelineSensors(timelineId);
  const { data: logs = [] } = useTimelineLogs(timelineId);
  const deleteTimeline = useDeleteTimeline();
  const updateTimeline = useUpdateTimeline();
  const removeEntry = useRemoveEntry();
  const createComparison = useCreateComparison();
  const toast = useToastStore.getState();

  const sensors = sensorData?.sensors || [];

  if (isLoading) return <LoadingState label="Loading timeline..." />;
  if (isError)
    return (
      <ErrorState
        title="Failed to load timeline"
        message={getErrorMessage(error)}
        onRetry={() => refetch()}
      />
    );
  if (!timeline) return <div className="p-6 text-slate-400">Timeline not found</div>;

  const startEdit = () => {
    setEditName(timeline.name);
    setEditing(true);
  };

  const saveEdit = () => {
    if (editName.trim()) {
      updateTimeline.mutate(
        { id: timelineId, name: editName.trim() },
        {
          onSuccess: () => toast.success("Timeline updated"),
          onError: (err) => toast.error(getErrorMessage(err)),
        }
      );
    }
    setEditing(false);
  };

  const handleStartComparison = () => {
    if (entries.length >= 2) {
      createComparison.mutate(
        { timelineId, mode: comparisonMode, left_entry_id: entries[0].id, right_entry_id: entries[1].id },
        {
          onSuccess: () => toast.success("Comparison created"),
          onError: (err) => toast.error(getErrorMessage(err)),
        }
      );
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => setView("list")} className="text-slate-400 hover:text-white">
            ← Back
          </button>
          {editing ? (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="bg-slate-800/50 border border-slate-700/50 rounded px-3 py-1 text-white"
                autoFocus
                onKeyDown={(e) => e.key === "Enter" && saveEdit()}
              />
              <button onClick={saveEdit} className="text-green-400 hover:text-green-300">✓</button>
              <button onClick={() => setEditing(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>
          ) : (
            <h2 className="text-xl font-bold text-white cursor-pointer hover:text-primary-400" onClick={startEdit}>
              {timeline.name}
            </h2>
          )}
          {timeline.favorite && <span className="text-yellow-400">★</span>}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (confirm("Delete this timeline?")) {
                deleteTimeline.mutate(timelineId, {
                  onSuccess: () => {
                    toast.success("Timeline deleted");
                    setView("list");
                  },
                  onError: (err) => toast.error(getErrorMessage(err)),
                });
              }
            }}
            className="btn-secondary text-red-400 hover:text-red-300"
          >
            Delete
          </button>
        </div>
      </div>

      {timeline.description && <p className="text-slate-400">{timeline.description}</p>}

      {/* Toolbar */}
      <TimelineToolbar
        groupBy={timeline.group_by as any}
        onGroupByChange={(g) => updateTimeline.mutate({ id: timelineId, group_by: g })}
        sortOrder={timeline.sort_order}
        onSortOrderChange={(s) => updateTimeline.mutate({ id: timelineId, sort_order: s })}
      />

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <DateFilter dateRange={dateRange} onDateRangeChange={setDateRange} />
        <SensorFilter sensors={sensors.map((s) => ({ name: s }))} selected={sensorFilter} onSelect={setSensorFilter} />
      </div>

      {/* Player */}
      {entries.length > 0 && (
        <TimelinePlayer
          entries={entries}
          currentIndex={playerIndex}
          onIndexChange={setPlayerIndex}
        />
      )}

      {/* Comparison */}
      <div className="flex items-center gap-3">
        <select
          value={comparisonMode}
          onChange={(e) => setComparisonMode(e.target.value as any)}
          className="bg-slate-800/50 border border-slate-700/50 rounded px-3 py-1.5 text-sm text-white"
        >
          <option value="side_by_side">Side by Side</option>
          <option value="swipe">Swipe</option>
          <option value="single">Single</option>
        </select>
        <button
          onClick={handleStartComparison}
          disabled={entries.length < 2}
          className="btn-primary disabled:opacity-50"
        >
          Compare
        </button>
      </div>

      {/* Entries */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-3">Entries ({entries.length})</h3>
        {entries.length === 0 ? (
          <div className="text-center py-8 bg-slate-800/30 rounded-lg border border-slate-700/50">
            <p className="text-slate-400">No entries in this timeline</p>
            <p className="text-sm text-slate-500 mt-1">Add datasets from the Datasets page</p>
          </div>
        ) : (
          <div className="space-y-2">
            {entries.map((entry: TimelineEntry, idx: number) => (
              <div
                key={entry.id}
                className={`bg-slate-800/50 border rounded-lg p-3 flex items-center justify-between cursor-pointer transition-colors ${
                  idx === playerIndex ? "border-primary-500/50 bg-primary-500/10" : "border-slate-700/50 hover:border-slate-600/50"
                }`}
                onClick={() => setPlayerIndex(idx)}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-slate-700/50 flex items-center justify-center text-sm text-slate-400">
                    {idx + 1}
                  </div>
                  <div>
                    <div className="text-white text-sm">
                      {entry.acquisition_date ? new Date(entry.acquisition_date).toLocaleDateString() : "No date"}
                    </div>
                          <div className="text-xs text-slate-400">{entry.sensor_name || "Unknown sensor"}</div>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm("Remove this entry?")) {
                      removeEntry.mutate(
                        { timelineId, entryId: entry.id },
                        {
                          onSuccess: () => toast.success("Entry removed"),
                          onError: (err) => toast.error(getErrorMessage(err)),
                        }
                      );
                    }
                  }}
                  className="text-slate-400 hover:text-red-400 p-1"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Logs */}
      {logs.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-3">Activity</h3>
          <div className="space-y-1">
            {logs.slice(0, 10).map((log) => (
              <div key={log.id} className="flex items-center gap-3 text-sm">
                <span className="text-slate-500 text-xs w-32">{new Date(log.timestamp).toLocaleString()}</span>
                <span className="text-slate-400">{log.action}</span>
                {log.details && <span className="text-slate-500">— {log.details}</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
