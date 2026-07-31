import type { ImageRegistration } from "../../types/registration";
import { useRegistrationMetrics } from "../../hooks/useRegistration";

interface MetricsPanelProps {
  registration: ImageRegistration;
}

export function MetricsPanel({ registration: reg }: MetricsPanelProps) {
  const { data: metrics = [], isLoading } = useRegistrationMetrics(reg.id);
  const latest = metrics.length > 0 ? metrics[0] : null;

  if (reg.status !== "completed") {
    return (
      <div className="h-full flex items-center justify-center text-gray-400 text-xs p-4">
        Registration must be completed to view metrics.
      </div>
    );
  }

  const gradeColor = (grade: string | null) => {
    if (!grade) return "text-gray-400";
    if (grade.startsWith("A")) return "text-green-400 font-bold";
    if (grade.startsWith("B")) return "text-blue-400 font-bold";
    if (grade.startsWith("C")) return "text-yellow-400 font-bold";
    return "text-red-400 font-bold";
  };

  const scoreBar = (score: number) => {
    const color =
      score >= 80 ? "bg-green-500" : score >= 60 ? "bg-blue-500" : score >= 40 ? "bg-yellow-500" : "bg-red-500";
    return (
      <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-gray-800 text-white">
      <div className="p-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-gray-200">Quality Metrics</h3>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4 text-xs">
        {isLoading ? (
          <div className="text-center text-gray-400">Loading...</div>
        ) : (
          <>
            {/* Overall Score */}
            <div>
              <h4 className="text-gray-400 mb-2">Overall Score</h4>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-gray-200">
                  {reg.confidence_score?.toFixed(1) || "N/A"}
                </span>
                <span className="text-gray-400 mb-1">/ 100</span>
              </div>
              {reg.confidence_score !== null && scoreBar(reg.confidence_score)}
              {latest && (
                <div className="mt-2">
                  <span className="text-gray-400">Grade: </span>
                  <span className={gradeColor(latest.quality_grade)}>
                    {latest.quality_grade}
                  </span>
                </div>
              )}
            </div>

            {/* Core Metrics */}
            <div>
              <h4 className="text-gray-400 mb-2">Core Metrics</h4>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-gray-900 p-2 rounded">
                  <div className="text-gray-400">RMSE</div>
                  <div className="text-gray-200 text-sm font-medium">
                    {reg.rmse?.toFixed(3) || "N/A"} px
                  </div>
                </div>
                <div className="bg-gray-900 p-2 rounded">
                  <div className="text-gray-400">Matched Points</div>
                  <div className="text-gray-200 text-sm font-medium">
                    {reg.matched_points || 0}
                  </div>
                </div>
                <div className="bg-gray-900 p-2 rounded">
                  <div className="text-gray-400">Inlier Count</div>
                  <div className="text-gray-200 text-sm font-medium">
                    {reg.inlier_count || 0}
                  </div>
                </div>
                <div className="bg-gray-900 p-2 rounded">
                  <div className="text-gray-400">Inlier Ratio</div>
                  <div className="text-gray-200 text-sm font-medium">
                    {((reg.inlier_ratio ?? 0) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Feature Detection */}
            {latest && (
              <div>
                <h4 className="text-gray-400 mb-2">Feature Detection</h4>
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-gray-900 p-2 rounded">
                    <div className="text-gray-400">Features (Ref)</div>
                    <div className="text-gray-200 text-sm font-medium">
                      {latest.features_detected_ref || 0}
                    </div>
                  </div>
                  <div className="bg-gray-900 p-2 rounded">
                    <div className="text-gray-400">Features (Tgt)</div>
                    <div className="text-gray-200 text-sm font-medium">
                      {latest.features_detected_tgt || 0}
                    </div>
                  </div>
                  <div className="bg-gray-900 p-2 rounded">
                    <div className="text-gray-400">Raw Matches</div>
                    <div className="text-gray-200 text-sm font-medium">
                      {latest.raw_matches || 0}
                    </div>
                  </div>
                  <div className="bg-gray-900 p-2 rounded">
                    <div className="text-gray-400">Inlier Matches</div>
                    <div className="text-gray-200 text-sm font-medium">
                      {latest.inlier_matches || 0}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Residual Analysis */}
            {latest && latest.max_residual !== null && (
              <div>
                <h4 className="text-gray-400 mb-2">Residual Analysis</h4>
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-gray-900 p-2 rounded">
                    <div className="text-gray-400">Max Residual</div>
                    <div className="text-gray-200 text-sm font-medium">
                      {latest.max_residual?.toFixed(3)} px
                    </div>
                  </div>
                  <div className="bg-gray-900 p-2 rounded">
                    <div className="text-gray-400">Median Residual</div>
                    <div className="text-gray-200 text-sm font-medium">
                      {latest.median_residual?.toFixed(3)} px
                    </div>
                  </div>
                  {latest.transform_determinant !== null && (
                    <div className="bg-gray-900 p-2 rounded col-span-2">
                      <div className="text-gray-400">Transform Determinant</div>
                      <div className="text-gray-200 text-sm font-medium">
                        {latest.transform_determinant?.toFixed(6)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* All History */}
            {metrics.length > 1 && (
              <div>
                <h4 className="text-gray-400 mb-2">Previous Results</h4>
                <div className="space-y-1">
                  {metrics.slice(1).map((m) => (
                    <div
                      key={m.id}
                      className="bg-gray-900 p-2 rounded flex items-center justify-between"
                    >
                      <span className="text-gray-300">
                        {new Date(m.created_at || "").toLocaleString()}
                      </span>
                      <span className={gradeColor(m.quality_grade)}>
                        {m.quality_grade} ({m.overall_score?.toFixed(1)})
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
