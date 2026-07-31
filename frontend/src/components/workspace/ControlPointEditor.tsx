import { useState } from "react";
import type {
  ImageRegistration,
  ControlPointCreateRequest,
} from "../../types/registration";
import {
  useControlPoints,
  useCreateControlPoint,
  useDeleteControlPoint,
  useDeleteAllControlPoints,
  useRunManualRegistration,
} from "../../hooks/useRegistration";

interface ControlPointEditorProps {
  registration: ImageRegistration;
}

export function ControlPointEditor({ registration: reg }: ControlPointEditorProps) {
  const [newPoint, setNewPoint] = useState<{
    ref_x: string;
    ref_y: string;
    target_x: string;
    target_y: string;
    label: string;
  }>({
    ref_x: "",
    ref_y: "",
    target_x: "",
    target_y: "",
    label: "",
  });

  const { data: points = [], isLoading } = useControlPoints(reg.id);
  const createMutation = useCreateControlPoint();
  const deleteMutation = useDeleteControlPoint();
  const deleteAllMutation = useDeleteAllControlPoints();
  const runManualMutation = useRunManualRegistration();

  const handleAdd = () => {
    const refX = parseFloat(newPoint.ref_x);
    const refY = parseFloat(newPoint.ref_y);
    const tgtX = parseFloat(newPoint.target_x);
    const tgtY = parseFloat(newPoint.target_y);

    if (isNaN(refX) || isNaN(refY) || isNaN(tgtX) || isNaN(tgtY)) return;

    const data: ControlPointCreateRequest = {
      ref_x: refX,
      ref_y: refY,
      target_x: tgtX,
      target_y: tgtY,
    };
    if (newPoint.label) data.label = newPoint.label;

    createMutation.mutate(
      { registrationId: reg.id, data },
      {
        onSuccess: () => {
          setNewPoint({ ref_x: "", ref_y: "", target_x: "", target_y: "", label: "" });
        },
      }
    );
  };

  const handleDelete = (pointId: string) => {
    if (confirm("Delete this control point?")) {
      deleteMutation.mutate({ registrationId: reg.id, pointId });
    }
  };

  const handleDeleteAll = () => {
    if (confirm(`Delete all ${points.length} control points?`)) {
      deleteAllMutation.mutate(reg.id);
    }
  };

  const handleRun = () => {
    if (points.length < 3) {
      alert("At least 3 control points are required for affine registration.");
      return;
    }
    runManualMutation.mutate({ registrationId: reg.id, resampling: reg.resampling });
  };

  return (
    <div className="h-full flex flex-col bg-gray-800 text-white">
      <div className="flex items-center justify-between p-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200">
          Control Points ({points.length})
        </h3>
        <div className="flex gap-1">
          {points.length > 0 && (
            <button
              onClick={handleDeleteAll}
              className="px-2 py-1 text-xs bg-red-600 hover:bg-red-500 rounded"
            >
              Clear
            </button>
          )}
          <button
            onClick={handleRun}
            disabled={points.length < 3 || runManualMutation.isPending}
            className="px-2 py-1 text-xs bg-green-600 hover:bg-green-500 rounded disabled:opacity-50"
          >
            {runManualMutation.isPending ? "Running..." : "Run"}
          </button>
        </div>
      </div>

      {/* Add new point form */}
      <div className="p-3 border-b border-gray-700 space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-gray-400">Ref X</label>
            <input
              type="number"
              step="0.1"
              value={newPoint.ref_x}
              onChange={(e) => setNewPoint({ ...newPoint, ref_x: e.target.value })}
              className="w-full px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
              placeholder="0.0"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">Ref Y</label>
            <input
              type="number"
              step="0.1"
              value={newPoint.ref_y}
              onChange={(e) => setNewPoint({ ...newPoint, ref_y: e.target.value })}
              className="w-full px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
              placeholder="0.0"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">Target X</label>
            <input
              type="number"
              step="0.1"
              value={newPoint.target_x}
              onChange={(e) =>
                setNewPoint({ ...newPoint, target_x: e.target.value })
              }
              className="w-full px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
              placeholder="0.0"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">Target Y</label>
            <input
              type="number"
              step="0.1"
              value={newPoint.target_y}
              onChange={(e) =>
                setNewPoint({ ...newPoint, target_y: e.target.value })
              }
              className="w-full px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
              placeholder="0.0"
            />
          </div>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newPoint.label}
            onChange={(e) => setNewPoint({ ...newPoint, label: e.target.value })}
            className="flex-1 px-2 py-1 text-xs bg-gray-700 border border-gray-600 rounded"
            placeholder="Label (optional)"
          />
          <button
            onClick={handleAdd}
            disabled={createMutation.isPending}
            className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-500 rounded disabled:opacity-50"
          >
            Add
          </button>
        </div>
      </div>

      {/* Points list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-gray-400 text-xs">Loading...</div>
        ) : points.length === 0 ? (
          <div className="p-4 text-center text-gray-400 text-xs">
            No control points. Add points using the form above.
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {points.map((pt) => (
              <div key={pt.id} className="p-2 flex items-center justify-between text-xs">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">#{pt.point_index}</span>
                    {pt.label && (
                      <span className="text-blue-400">{pt.label}</span>
                    )}
                    <span
                      className={
                        pt.is_inlier ? "text-green-400" : "text-red-400"
                      }
                    >
                      {pt.is_inlier ? "●" : "○"}
                    </span>
                  </div>
                  <div className="text-gray-400 mt-1">
                    Ref: ({pt.ref_x.toFixed(1)}, {pt.ref_y.toFixed(1)}) →
                    Tgt: ({pt.target_x.toFixed(1)}, {pt.target_y.toFixed(1)})
                    {pt.residual !== null && (
                      <span className="ml-2">
                        Res: {pt.residual.toFixed(2)}px
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(pt.id)}
                  className="text-gray-400 hover:text-red-400 ml-2"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
