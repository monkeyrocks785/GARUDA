import { useState } from "react";
import { useProjects, useProjectStats } from "../hooks/useProjects";
import { useProjectStore } from "../store/useProjectStore";
import ProjectCard from "../components/ProjectCard";
import CreateProjectModal from "../components/CreateProjectModal";
import ProjectSearch from "../components/ProjectSearch";

export default function Projects() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const {
    searchQuery,
    statusFilter,
    sortBy,
    sortOrder,
    showArchived,
    setShowArchived,
  } = useProjectStore();

  const { data: projectsData, isLoading } = useProjects({
    search: searchQuery || undefined,
    include_archived: showArchived,
  });

  const { data: stats } = useProjectStats();

  // Client-side filtering and sorting
  const filteredProjects = (projectsData?.projects || [])
    .filter((p) => {
      if (statusFilter && p.status !== statusFilter) return false;
      return true;
    })
    .sort((a, b) => {
      const aVal = a[sortBy] || "";
      const bVal = b[sortBy] || "";
      const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortOrder === "asc" ? comparison : -comparison;
    });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Projects</h1>
          <p className="text-slate-400 mt-1">
            {stats ? `${stats.total} projects` : "Manage your geospatial projects"}
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Project
        </button>
      </div>

      {/* Quick Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
            <p className="text-sm text-slate-400">Total</p>
            <p className="text-2xl font-bold text-white">{stats.total}</p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
            <p className="text-sm text-slate-400">Favorites</p>
            <p className="text-2xl font-bold text-yellow-400">{stats.favorites}</p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
            <p className="text-sm text-slate-400">Processing</p>
            <p className="text-2xl font-bold text-blue-400">{stats.processing}</p>
          </div>
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
            <p className="text-sm text-slate-400">Archived</p>
            <p className="text-2xl font-bold text-slate-400">{stats.archived}</p>
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <ProjectSearch />

      {/* Archived Toggle */}
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
            className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-primary-500 focus:ring-primary-500"
          />
          <span className="text-sm text-slate-400">Show archived projects</span>
        </label>
      </div>

      {/* Projects Grid/List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700/50 flex items-center justify-center">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">
            {searchQuery ? "No matching projects" : "No projects yet"}
          </h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto mb-4">
            {searchQuery
              ? "Try adjusting your search criteria"
              : "Create your first project to start analyzing geospatial data and imagery."}
          </p>
          {!searchQuery && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
            >
              Create Project
            </button>
          )}
        </div>
      ) : (
        <div
          className={
            filteredProjects.length === 0
              ? ""
              : "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          }
        >
          {filteredProjects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  );
}
