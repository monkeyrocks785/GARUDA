import { useState } from "react";
import { useCreateTimeline } from "../../hooks/useTemporal";
import { GROUP_BY_OPTIONS } from "../../types/temporal";
import type { GroupBy } from "../../types/temporal";
import { useToastStore } from "../../store/useToastStore";
import { getErrorMessage } from "../../utils/errorMessage";

interface Props {
  onDone: () => void;
}

export default function CreateTimeline({ onDone }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [groupBy, setGroupBy] = useState<GroupBy>("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

  const createTimeline = useCreateTimeline();
  const toast = useToastStore.getState();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createTimeline.mutate(
      { name: name.trim(), description: description.trim() || undefined, group_by: groupBy, sort_order: sortOrder },
      {
        onSuccess: () => {
          toast.success("Timeline created");
          onDone();
        },
        onError: (err) => toast.error(getErrorMessage(err)),
      }
    );
  };

  return (
    <div className="p-6 max-w-lg">
      <h2 className="text-xl font-bold text-white mb-6">New Timeline</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-slate-400 mb-1">Name *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white"
            autoFocus
          />
        </div>
        <div>
          <label className="block text-sm text-slate-400 mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white h-20"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Group By</label>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value as GroupBy)}
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white"
            >
              {GROUP_BY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Sort Order</label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as "asc" | "desc")}
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-4 py-2 text-white"
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </div>
        </div>
        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={!name.trim() || createTimeline.isPending} className="btn-primary">
            {createTimeline.isPending ? "Creating..." : "Create Timeline"}
          </button>
          <button type="button" onClick={onDone} className="btn-secondary">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
