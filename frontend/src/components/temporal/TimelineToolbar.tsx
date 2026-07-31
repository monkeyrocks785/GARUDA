import type { GroupBy } from "../../types/temporal";
import { GROUP_BY_OPTIONS } from "../../types/temporal";

interface Props {
  groupBy: GroupBy;
  onGroupByChange: (g: GroupBy) => void;
  sortOrder: string;
  onSortOrderChange: (s: "asc" | "desc") => void;
}

export default function TimelineToolbar({ groupBy, onGroupByChange, sortOrder, onSortOrderChange }: Props) {
  return (
    <div className="flex items-center gap-4 flex-wrap">
      <div className="flex items-center gap-2">
        <label className="text-sm text-slate-400">Group:</label>
        <select
          value={groupBy}
          onChange={(e) => onGroupByChange(e.target.value as GroupBy)}
          className="bg-slate-800/50 border border-slate-700/50 rounded px-3 py-1.5 text-sm text-white"
        >
          {GROUP_BY_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <label className="text-sm text-slate-400">Sort:</label>
        <button
          onClick={() => onSortOrderChange(sortOrder === "asc" ? "desc" : "asc")}
          className="bg-slate-800/50 border border-slate-700/50 rounded px-3 py-1.5 text-sm text-white hover:bg-slate-700/50"
        >
          {sortOrder === "asc" ? "↑ Ascending" : "↓ Descending"}
        </button>
      </div>
    </div>
  );
}
