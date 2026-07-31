import type { ImageRegistration } from "../../types/registration";
import {
  useRegistrationMetrics,
  useRegistrationHistory,
} from "../../hooks/useRegistration";

interface RegistrationViewerProps {
  registration: ImageRegistration;
  onClose: () => void;
}

export function RegistrationViewer({
  registration: reg,
  onClose,
}: RegistrationViewerProps) {
  const { data: metrics = [] } = useRegistrationMetrics(reg.id);
  const { data: history = [] } = useRegistrationHistory(reg.id);

  const latestMetrics = metrics.length > 0 ? metrics[0] : null;

  const statusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-900 text-green-300";
      case "running":
        return "bg-blue-900 text-blue-300";
      case "failed":
        return "bg-red-900 text-red-300";
      default:
        return "bg-gray-700 text-gray-300";
    }
  };

  const gradeColor = (grade: string | null | undefined) => {
    if (!grade) return "text-gray-400";
    if (grade.startsWith("A")) return "text-green-400";
    if (grade.startsWith("B")) return "text-blue-400";
    if (grade.startsWith("C")) return "text-yellow-400";
    return "text-red-400";
  };

  return (
    <div className="h-full flex flex-col bg-gray-800 text-white">
      <div className="flex items-center justify-between p-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200">{reg.name}</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-white">
          ×
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4 text-xs">
        {/* Status */}
        <div>
          <span className={`px-2 py-1 rounded text-xs ${statusColor(reg.status)}`}>
            {reg.status}
          </span>
          {reg.error_message && (
            <p className="text-red-400 mt-1">{reg.error_message}</p>
          )}
        </div>

        {/* Configuration */}
        <div>
          <h4 className="text-gray-400 mb-1">Configuration</h4>
          <div className="grid grid-cols-2 gap-1">
            <span className="text-gray-400">Mode:</span>
            <span className="text-gray-200">{reg.mode}</span>
            <span className="text-gray-400">Detector:</span>
            <span className="text-gray-200">{reg.feature_detector}</span>
            <span className="text-gray-400">Transform:</span>
            <span className="text-gray-200">{reg.transform_type}</span>
            <span className="text-gray-400">Resampling:</span>
            <span className="text-gray-200">{reg.resampling}</span>
          </div>
        </div>

        {/* Image Info */}
        <div>
          <h4 className="text-gray-400 mb-1">Reference Image</h4>
          <p className="text-gray-200 break-all">{reg.reference_path}</p>
          {reg.ref_width && (
            <p className="text-gray-400 mt-1">
              {reg.ref_width} × {reg.ref_height} px
            </p>
          )}
        </div>

        <div>
          <h4 className="text-gray-400 mb-1">Target Image</h4>
          <p className="text-gray-200 break-all">{reg.target_path}</p>
          {reg.tgt_width && (
            <p className="text-gray-400 mt-1">
              {reg.tgt_width} × {reg.tgt_height} px
            </p>
          )}
        </div>

        {/* Quality Metrics */}
        {reg.status === "completed" && (
          <div>
            <h4 className="text-gray-400 mb-1">Quality Metrics</h4>
            <div className="grid grid-cols-2 gap-1">
              <span className="text-gray-400">Score:</span>
              <span className="text-gray-200">
                {reg.confidence_score?.toFixed(1)} / 100
              </span>
              <span className="text-gray-400">Grade:</span>
              <span className={gradeColor(latestMetrics?.quality_grade)}>
                {latestMetrics?.quality_grade || "N/A"}
              </span>
              <span className="text-gray-400">RMSE:</span>
              <span className="text-gray-200">
                {reg.rmse?.toFixed(3)} px
              </span>
              <span className="text-gray-400">Matched Points:</span>
              <span className="text-gray-200">{reg.matched_points}</span>
              <span className="text-gray-400">Inliers:</span>
              <span className="text-gray-200">
                {reg.inlier_count} ({((reg.inlier_ratio ?? 0) * 100).toFixed(1)}%)
              </span>
              {latestMetrics && (
                <>
                  <span className="text-gray-400">Features (Ref):</span>
                  <span className="text-gray-200">
                    {latestMetrics.features_detected_ref}
                  </span>
                  <span className="text-gray-400">Features (Tgt):</span>
                  <span className="text-gray-200">
                    {latestMetrics.features_detected_tgt}
                  </span>
                  {latestMetrics.max_residual !== null && (
                    <>
                      <span className="text-gray-400">Max Residual:</span>
                      <span className="text-gray-200">
                        {latestMetrics.max_residual?.toFixed(3)} px
                      </span>
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* Output */}
        {reg.output_path && (
          <div>
            <h4 className="text-gray-400 mb-1">Output</h4>
            <p className="text-gray-200 break-all">{reg.output_path}</p>
          </div>
        )}

        {/* Transform Matrix */}
        {reg.transform_matrix && (
          <div>
            <h4 className="text-gray-400 mb-1">Transform Matrix</h4>
            <pre className="text-gray-200 bg-gray-900 p-2 rounded overflow-x-auto">
              {reg.transform_matrix
                .map((row) => row.map((v) => v.toFixed(6).padStart(12)).join(" "))
                .join("\n")}
            </pre>
          </div>
        )}

        {/* History */}
        {history.length > 0 && (
          <div>
            <h4 className="text-gray-400 mb-1">History</h4>
            <div className="space-y-1">
              {history.slice(0, 5).map((h) => (
                <div key={h.id} className="flex items-center gap-2 text-xs">
                  <span className={`${
                    h.status === "completed"
                      ? "text-green-400"
                      : h.status === "failed"
                      ? "text-red-400"
                      : "text-gray-400"
                  }`}>
                    {h.status === "completed" ? "✓" : h.status === "failed" ? "✗" : "○"}
                  </span>
                  <span className="text-gray-300">{h.operation}</span>
                  {h.execution_time_ms !== null && (
                    <span className="text-gray-500">
                      ({h.execution_time_ms}ms)
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Timestamps */}
        <div>
          <h4 className="text-gray-400 mb-1">Timestamps</h4>
          <div className="grid grid-cols-2 gap-1">
            <span className="text-gray-400">Created:</span>
            <span className="text-gray-200">
              {reg.created_at ? new Date(reg.created_at).toLocaleString() : "N/A"}
            </span>
            {reg.completed_at && (
              <>
                <span className="text-gray-400">Completed:</span>
                <span className="text-gray-200">
                  {new Date(reg.completed_at).toLocaleString()}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
