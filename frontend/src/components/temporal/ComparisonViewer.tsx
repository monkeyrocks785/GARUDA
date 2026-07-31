import { useState, useEffect } from "react";
import { useUpdateComparison } from "../../hooks/useTemporal";
import type { ComparisonSession, TimelineEntry } from "../../types/temporal";

interface Props {
  timelineId: string;
  session: ComparisonSession;
  entries: TimelineEntry[];
}

export default function ComparisonViewer({ timelineId, session, entries }: Props) {
  const [swipePos, setSwipePos] = useState(session.swipe_position);
  const [opacity, setOpacity] = useState(session.opacity);
  const updateComparison = useUpdateComparison();

  useEffect(() => {
    setSwipePos(session.swipe_position);
    setOpacity(session.opacity);
  }, [session]);

  const handleSwipeChange = (val: number) => {
    setSwipePos(val);
    updateComparison.mutate({
      timelineId,
      sessionId: session.id,
      swipe_position: val,
    });
  };

  const handleOpacityChange = (val: number) => {
    setOpacity(val);
    updateComparison.mutate({
      timelineId,
      sessionId: session.id,
      opacity: val,
    });
  };

  const leftEntry = entries.find((e) => e.id === session.left_entry_id);
  const rightEntry = entries.find((e) => e.id === session.right_entry_id);

  const formatDate = (d: string | null) => {
    if (!d) return "N/A";
    return new Date(d).toLocaleDateString();
  };

  if (session.mode === "side_by_side") {
    return (
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
        <div className="text-sm text-slate-400 mb-3">Side-by-Side Comparison</div>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-600/50">
            <div className="text-white font-medium mb-2">{leftEntry ? formatDate(leftEntry.acquisition_date) : "Left"}</div>
            <div className="text-sm text-slate-400">{leftEntry?.sensor_name || "Select entry"}</div>
            <div className="mt-4 bg-slate-800 rounded h-40 flex items-center justify-center text-slate-500">
              Map View
            </div>
          </div>
          <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-600/50">
            <div className="text-white font-medium mb-2">{rightEntry ? formatDate(rightEntry.acquisition_date) : "Right"}</div>
            <div className="text-sm text-slate-400">{rightEntry?.sensor_name || "Select entry"}</div>
            <div className="mt-4 bg-slate-800 rounded h-40 flex items-center justify-center text-slate-500">
              Map View
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Swipe mode
  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
      <div className="text-sm text-slate-400 mb-3">Swipe Comparison</div>
      <div className="relative bg-slate-900/50 rounded-lg overflow-hidden">
        <div className="bg-slate-800 rounded h-64 flex items-center justify-center text-slate-500">
          Swipe Map View
        </div>
        <div
          className="absolute top-0 bottom-0 w-1 bg-primary-500 cursor-ew-resize"
          style={{ left: `${swipePos}%` }}
        />
      </div>
      <div className="mt-4 space-y-3">
        <div className="flex items-center gap-4">
          <label className="text-sm text-slate-400 w-24">Position:</label>
          <input
            type="range"
            min={0}
            max={100}
            value={swipePos}
            onChange={(e) => handleSwipeChange(parseFloat(e.target.value))}
            className="flex-1 accent-primary-500"
          />
          <span className="text-sm text-slate-400 w-12 text-right">{Math.round(swipePos)}%</span>
        </div>
        <div className="flex items-center gap-4">
          <label className="text-sm text-slate-400 w-24">Opacity:</label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={opacity}
            onChange={(e) => handleOpacityChange(parseFloat(e.target.value))}
            className="flex-1 accent-primary-500"
          />
          <span className="text-sm text-slate-400 w-12 text-right">{Math.round(opacity * 100)}%</span>
        </div>
      </div>
    </div>
  );
}
