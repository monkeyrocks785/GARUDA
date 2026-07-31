interface Props {
  dateRange: { from: string | null; to: string | null };
  onDateRangeChange: (range: { from: string | null; to: string | null }) => void;
}

export default function DateFilter({ dateRange, onDateRangeChange }: Props) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <label className="text-sm text-slate-400">From:</label>
        <input
          type="date"
          value={dateRange.from || ""}
          onChange={(e) => onDateRangeChange({ ...dateRange, from: e.target.value || null })}
          className="bg-slate-800/50 border border-slate-700/50 rounded px-3 py-1.5 text-sm text-white"
        />
      </div>
      <div className="flex items-center gap-2">
        <label className="text-sm text-slate-400">To:</label>
        <input
          type="date"
          value={dateRange.to || ""}
          onChange={(e) => onDateRangeChange({ ...dateRange, to: e.target.value || null })}
          className="bg-slate-800/50 border border-slate-700/50 rounded px-3 py-1.5 text-sm text-white"
        />
      </div>
      {(dateRange.from || dateRange.to) && (
        <button
          onClick={() => onDateRangeChange({ from: null, to: null })}
          className="text-sm text-slate-400 hover:text-white"
        >
          Clear
        </button>
      )}
    </div>
  );
}
