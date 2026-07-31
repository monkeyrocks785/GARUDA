import { useNavigate } from "react-router-dom";
import { useRecentProjects, useProjectStats } from "../hooks/useProjects";
import { formatShortDate } from "../utils/format";
import { getErrorMessage } from "../utils/errorMessage";
import ErrorState from "../components/ui/ErrorState";

export default function Dashboard() {
  const navigate = useNavigate();
  const {
    data: recentProjects,
    isLoading: projectsLoading,
    isError: projectsError,
    error: projectsErrorObj,
    refetch: refetchProjects,
  } = useRecentProjects(5);
  const {
    data: stats,
    isLoading: statsLoading,
    isError: statsError,
    error: statsErrorObj,
    refetch: refetchStats,
  } = useProjectStats();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 mt-1">
          Welcome to GARUDA - Geospatial Intelligence Platform
        </p>
      </div>

      {/* Stats Cards */}
      {statsError ? (
        <ErrorState
          compact
          title="Failed to load stats"
          message={getErrorMessage(statsErrorObj)}
          onRetry={() => refetchStats()}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
          {
            label: "Projects",
            value: statsLoading ? "…" : stats?.total?.toString() || "0",
            color: "bg-primary-600",
            icon: "📁",
          },
          {
            label: "Favorites",
            value: statsLoading ? "…" : stats?.favorites?.toString() || "0",
            color: "bg-yellow-600",
            icon: "⭐",
          },
          {
            label: "Processing",
            value: statsLoading ? "…" : stats?.processing?.toString() || "0",
            color: "bg-blue-600",
            icon: "⚙️",
          },
          {
            label: "Archived",
            value: statsLoading ? "…" : stats?.archived?.toString() || "0",
            color: "bg-slate-600",
            icon: "📦",
          },
        ].map((card) => (
          <div
            key={card.label}
            className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5"
          >
            <div className="flex items-center justify-between">
                <div>
                <p className="text-sm text-slate-400">{card.label}</p>
                <p className="text-3xl font-bold text-white mt-1">{card.value}</p>
              </div>
              <div
                className={`w-12 h-12 ${card.color} rounded-lg flex items-center justify-center`}
              >
                <span className="text-xl">{card.icon}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Projects */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Recent Projects</h3>
            <button
              onClick={() => navigate("/projects")}
              className="text-sm text-primary-400 hover:text-primary-300"
            >
              View all
            </button>
          </div>
          {projectsLoading ? (
            <p className="text-slate-400 text-sm">Loading projects...</p>
          ) : projectsError ? (
            <ErrorState
              compact
              title="Failed to load projects"
              message={getErrorMessage(projectsErrorObj)}
              onRetry={() => refetchProjects()}
            />
          ) : recentProjects && recentProjects.length > 0 ? (
            <div className="space-y-3">
              {recentProjects.map((project) => (
                <div
                  key={project.id}
                  onClick={() => navigate(`/projects/${project.id}`)}
                  className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg cursor-pointer hover:bg-slate-700/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary-600/20 flex items-center justify-center">
                      <span className="text-lg">📁</span>
                    </div>
                    <div>
                      <p className="text-white font-medium">{project.name}</p>
                      <p className="text-xs text-slate-400">
                        {project.last_opened_at
                          ? `Opened ${formatShortDate(project.last_opened_at)}`
                          : "Never opened"}
                      </p>
                    </div>
                  </div>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      project.status === "active"
                        ? "bg-green-500"
                        : project.status === "processing"
                        ? "bg-blue-500"
                        : "bg-slate-500"
                    }`}
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-400 text-sm">No recent projects.</p>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button
              onClick={() => navigate("/projects")}
              className="w-full flex items-center gap-3 p-3 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-primary-600 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <div>
                <p className="text-white font-medium">Create New Project</p>
                <p className="text-xs text-slate-400">Start a new geospatial analysis</p>
              </div>
            </button>
            <button
              onClick={() => navigate("/projects")}
              className="w-full flex items-center gap-3 p-3 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-yellow-600 flex items-center justify-center">
                <span className="text-lg">⭐</span>
              </div>
              <div>
                <p className="text-white font-medium">View Favorites</p>
                <p className="text-xs text-slate-400">Access your favorite projects</p>
              </div>
            </button>
            <button
              onClick={() => navigate("/settings")}
              className="w-full flex items-center gap-3 p-3 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-slate-600 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <p className="text-white font-medium">Settings</p>
                <p className="text-xs text-slate-400">Configure your instance</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
