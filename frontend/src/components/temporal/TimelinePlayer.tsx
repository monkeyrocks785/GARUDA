import { useState, useEffect, useCallback } from "react";
import type { TimelineEntry } from "../../types/temporal";

interface Props {
  entries: TimelineEntry[];
  currentIndex: number;
  onIndexChange: (index: number) => void;
  speed?: number;
  loop?: boolean;
}

export default function TimelinePlayer({ entries, currentIndex, onIndexChange, speed = 1000, loop = false }: Props) {
  const [playing, setPlaying] = useState(false);

  const next = useCallback(() => {
    if (currentIndex < entries.length - 1) {
      onIndexChange(currentIndex + 1);
    } else if (loop) {
      onIndexChange(0);
    } else {
      setPlaying(false);
    }
  }, [currentIndex, entries.length, loop, onIndexChange]);

  const prev = useCallback(() => {
    if (currentIndex > 0) {
      onIndexChange(currentIndex - 1);
    }
  }, [currentIndex, onIndexChange]);

  useEffect(() => {
    if (!playing) return;
    const timer = setTimeout(next, speed);
    return () => clearTimeout(timer);
  }, [playing, currentIndex, next, speed]);

  if (entries.length === 0) return null;

  const entry = entries[currentIndex];
  const dateStr = entry.acquisition_date ? new Date(entry.acquisition_date).toLocaleDateString() : "Unknown date";

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-white font-medium">{dateStr}</div>
          <div className="text-sm text-slate-400">{entry.sensor_name || "Unknown sensor"}</div>
        </div>
        <div className="text-sm text-slate-400">
          {currentIndex + 1} / {entries.length}
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-slate-700 rounded-full h-2 mb-4">
        <div
          className="bg-primary-500 h-2 rounded-full transition-all"
          style={{ width: `${((currentIndex + 1) / entries.length) * 100}%` }}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-3">
        <button onClick={() => onIndexChange(0)} className="p-2 hover:bg-slate-700/50 rounded text-slate-400" title="First">
          ⟪
        </button>
        <button onClick={prev} disabled={currentIndex === 0} className="p-2 hover:bg-slate-700/50 rounded text-slate-400 disabled:opacity-30" title="Previous">
          ◀
        </button>
        <button
          onClick={() => setPlaying(!playing)}
          className="p-3 bg-primary-600 hover:bg-primary-700 rounded-full text-white"
        >
          {playing ? "⏸" : "▶"}
        </button>
        <button onClick={next} disabled={currentIndex >= entries.length - 1 && !loop} className="p-2 hover:bg-slate-700/50 rounded text-slate-400 disabled:opacity-30" title="Next">
          ▶
        </button>
        <button onClick={() => onIndexChange(entries.length - 1)} className="p-2 hover:bg-slate-700/50 rounded text-slate-400" title="Last">
          ⟫
        </button>
      </div>

      {/* Timeline slider */}
      <input
        type="range"
        min={0}
        max={entries.length - 1}
        value={currentIndex}
        onChange={(e) => onIndexChange(parseInt(e.target.value))}
        className="w-full mt-4 accent-primary-500"
      />
    </div>
  );
}
