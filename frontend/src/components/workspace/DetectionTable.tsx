import { useState } from "react";
import {
  useJobDetections,
  useReviewDetection,
  useAddDetectionNotes,
} from "../../hooks/useIntelligence";

interface DetectionTableProps {
  jobId: string | null;
}

export default function DetectionTable({ jobId }: DetectionTableProps) {
  const [classFilter, setClassFilter] = useState("");
  const [reviewFilter, setReviewFilter] = useState("");
  const [minConf, setMinConf] = useState(0);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [editingNotes, setEditingNotes] = useState<string | null>(null);
  const [notesText, setNotesText] = useState("");

  const { data: detections = [], isLoading } = useJobDetections(jobId, {
    class_name: classFilter || undefined,
    review_status: reviewFilter || undefined,
    min_confidence: minConf || undefined,
  });

  const reviewDetection = useReviewDetection();
  const addNotes = useAddDetectionNotes();

  const handleReview = (detId: string, status: string) => {
    reviewDetection.mutate({ detectionId: detId, data: { review_status: status } });
  };

  const handleSaveNotes = (detId: string) => {
    addNotes.mutate({ detectionId: detId, notes: notesText });
    setEditingNotes(null);
    setNotesText("");
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const reviewBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: "bg-slate-600 text-slate-300",
      accepted: "bg-emerald-700 text-emerald-200",
      rejected: "bg-red-700 text-red-200",
      uncertain: "bg-yellow-700 text-yellow-200",
    };
    return colors[status] || "bg-slate-600 text-slate-300";
  };

  if (!jobId) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 text-sm">
        Select a job to view detections
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-800">
      <div className="p-3 border-b border-slate-700 space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">
            Detections ({detections.length})
          </h3>
          {selectedIds.size > 0 && (
            <span className="text-[10px] text-blue-400">{selectedIds.size} selected</span>
          )}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Class filter"
            value={classFilter}
            onChange={(e) => setClassFilter(e.target.value)}
            className="w-24 px-2 py-1 text-[11px] bg-slate-700 border border-slate-600 rounded text-slate-300"
          />
          <select
            value={reviewFilter}
            onChange={(e) => setReviewFilter(e.target.value)}
            className="px-2 py-1 text-[11px] bg-slate-700 border border-slate-600 rounded text-slate-300"
          >
            <option value="">All reviews</option>
            <option value="pending">Pending</option>
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
            <option value="uncertain">Uncertain</option>
          </select>
          <input
            type="number"
            step="0.1"
            min="0"
            max="1"
            placeholder="Min conf"
            value={minConf}
            onChange={(e) => setMinConf(parseFloat(e.target.value) || 0)}
            className="w-20 px-2 py-1 text-[11px] bg-slate-700 border border-slate-600 rounded text-slate-300"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-slate-500 text-sm">Loading...</div>
        ) : detections.length === 0 ? (
          <div className="p-4 text-center text-slate-500 text-sm">No detections found.</div>
        ) : (
          <table className="w-full text-[11px]">
            <thead className="bg-slate-750 sticky top-0">
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="p-2 w-6">
                  <input
                    type="checkbox"
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedIds(new Set(detections.map((d) => d.id)));
                      } else {
                        setSelectedIds(new Set());
                      }
                    }}
                  />
                </th>
                <th className="p-2">Class</th>
                <th className="p-2">Conf</th>
                <th className="p-2">Review</th>
                <th className="p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {detections.map((det) => (
                <tr
                  key={det.id}
                  className="border-b border-slate-700/50 hover:bg-slate-750"
                >
                  <td className="p-2">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(det.id)}
                      onChange={() => toggleSelect(det.id)}
                    />
                  </td>
                  <td className="p-2 text-slate-300">{det.class_name}</td>
                  <td className="p-2 text-slate-400">{(det.confidence * 100).toFixed(1)}%</td>
                  <td className="p-2">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${reviewBadge(det.review_status)}`}>
                      {det.review_status}
                    </span>
                  </td>
                  <td className="p-2">
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleReview(det.id, "accepted")}
                        className="px-1.5 py-0.5 text-[9px] bg-emerald-700 hover:bg-emerald-600 rounded"
                      >
                        Accept
                      </button>
                      <button
                        onClick={() => handleReview(det.id, "rejected")}
                        className="px-1.5 py-0.5 text-[9px] bg-red-700 hover:bg-red-600 rounded"
                      >
                        Reject
                      </button>
                      <button
                        onClick={() => handleReview(det.id, "uncertain")}
                        className="px-1.5 py-0.5 text-[9px] bg-yellow-700 hover:bg-yellow-600 rounded"
                      >
                        ?
                      </button>
                      <button
                        onClick={() => {
                          setEditingNotes(det.id);
                          setNotesText(det.reviewer_notes || "");
                        }}
                        className="px-1.5 py-0.5 text-[9px] bg-slate-600 hover:bg-slate-500 rounded"
                      >
                        Notes
                      </button>
                    </div>
                    {editingNotes === det.id && (
                      <div className="mt-1 flex gap-1">
                        <input
                          type="text"
                          value={notesText}
                          onChange={(e) => setNotesText(e.target.value)}
                          className="flex-1 px-1 py-0.5 text-[10px] bg-slate-700 border border-slate-600 rounded text-slate-300"
                          placeholder="Notes..."
                        />
                        <button
                          onClick={() => handleSaveNotes(det.id)}
                          className="px-1.5 py-0.5 text-[9px] bg-blue-600 rounded"
                        >
                          Save
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
