import { useState } from "react";
import {
  useJobDetections,
  useReviewDetection,
  useAddDetectionNotes,
  useEditDetectionGeometry,
} from "../../hooks/useIntelligence";

interface ReviewPanelProps {
  jobId: string | null;
}

export default function ReviewPanel({ jobId }: ReviewPanelProps) {
  const [selectedDetId, setSelectedDetId] = useState<string | null>(null);
  const [notesText, setNotesText] = useState("");
  const [showEditGeo, setShowEditGeo] = useState(false);
  const [geoText, setGeoText] = useState("");

  const { data: detections = [] } = useJobDetections(jobId, {
    review_status: "pending",
  });
  const reviewDetection = useReviewDetection();
  const addNotes = useAddDetectionNotes();
  const editGeometry = useEditDetectionGeometry();

  const selected = detections.find((d) => d.id === selectedDetId);

  const handleReview = (status: string) => {
    if (!selectedDetId) return;
    reviewDetection.mutate({
      detectionId: selectedDetId,
      data: { review_status: status },
    });
  };

  const handleSaveNotes = () => {
    if (!selectedDetId) return;
    addNotes.mutate({ detectionId: selectedDetId, notes: notesText });
  };

  const handleSaveGeometry = () => {
    if (!selectedDetId || !geoText) return;
    try {
      const geometry = JSON.parse(geoText);
      editGeometry.mutate({ detectionId: selectedDetId, geometry });
      setShowEditGeo(false);
    } catch {
      alert("Invalid JSON geometry");
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-800">
      <div className="p-3 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-slate-200">
          Review ({detections.length} pending)
        </h3>
      </div>

      <div className="flex flex-1 min-h-0">
        <div className="w-1/3 border-r border-slate-700 overflow-y-auto">
          {detections.length === 0 ? (
            <div className="p-4 text-center text-slate-500 text-sm">
              No pending detections
            </div>
          ) : (
            detections.map((det) => (
              <button
                key={det.id}
                onClick={() => {
                  setSelectedDetId(det.id);
                  setNotesText(det.reviewer_notes || "");
                }}
                className={`w-full text-left p-2 border-b border-slate-700 text-[11px] ${
                  selectedDetId === det.id
                    ? "bg-blue-900/30 border-l-2 border-l-blue-500"
                    : "hover:bg-slate-750"
                }`}
              >
                <div className="text-slate-300 font-medium">{det.class_name}</div>
                <div className="text-slate-500">
                  {(det.confidence * 100).toFixed(1)}%
                </div>
              </button>
            ))
          )}
        </div>

        <div className="flex-1 p-3 overflow-y-auto">
          {selected ? (
            <div className="space-y-3">
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Class</div>
                <div className="text-sm text-slate-200">{selected.class_name}</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Confidence</div>
                <div className="text-sm text-slate-200">
                  {(selected.confidence * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Bounding Box</div>
                <div className="text-xs text-slate-400 font-mono">
                  [{selected.bbox_min_x.toFixed(1)}, {selected.bbox_min_y.toFixed(1)},
                  {selected.bbox_max_x.toFixed(1)}, {selected.bbox_max_y.toFixed(1)}]
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Area</div>
                <div className="text-xs text-slate-400">{selected.area.toFixed(1)} px²</div>
              </div>

              <div>
                <div className="text-[10px] text-slate-500 uppercase mb-1">Review Decision</div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleReview("accepted")}
                    className="px-3 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white rounded"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => handleReview("rejected")}
                    className="px-3 py-1.5 text-xs bg-red-600 hover:bg-red-500 text-white rounded"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => handleReview("uncertain")}
                    className="px-3 py-1.5 text-xs bg-yellow-600 hover:bg-yellow-500 text-white rounded"
                  >
                    Uncertain
                  </button>
                </div>
              </div>

              <div>
                <div className="text-[10px] text-slate-500 uppercase mb-1">Notes</div>
                <textarea
                  value={notesText}
                  onChange={(e) => setNotesText(e.target.value)}
                  className="w-full px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-300 h-16 resize-none"
                  placeholder="Add analyst notes..."
                />
                <button
                  onClick={handleSaveNotes}
                  className="mt-1 px-2 py-1 text-[10px] bg-blue-600 hover:bg-blue-500 text-white rounded"
                >
                  Save Notes
                </button>
              </div>

              <div>
                <div className="text-[10px] text-slate-500 uppercase mb-1">Edit Geometry</div>
                {showEditGeo ? (
                  <div>
                    <textarea
                      value={geoText}
                      onChange={(e) => setGeoText(e.target.value)}
                      className="w-full px-2 py-1 text-[10px] font-mono bg-slate-700 border border-slate-600 rounded text-slate-300 h-20 resize-none"
                      placeholder='{"type": "Polygon", "coordinates": [...]}'
                    />
                    <div className="flex gap-1 mt-1">
                      <button
                        onClick={handleSaveGeometry}
                        className="px-2 py-1 text-[10px] bg-blue-600 rounded text-white"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setShowEditGeo(false)}
                        className="px-2 py-1 text-[10px] bg-slate-600 rounded text-white"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => {
                      setGeoText(selected.geometry_json);
                      setShowEditGeo(true);
                    }}
                    className="px-2 py-1 text-[10px] bg-slate-600 hover:bg-slate-500 text-white rounded"
                  >
                    Edit Geometry
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 text-sm">
              Select a detection to review
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
