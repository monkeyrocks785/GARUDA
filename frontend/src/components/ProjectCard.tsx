import { useNavigate } from "react-router-dom";
import { useToggleFavorite } from "../hooks/useProjects";
import type { Project } from "../types";
import { parseTagArray } from "../utils/json";

interface ProjectCardProps {
  project: Project;
  selected?: boolean;
  onSelect?: (id: string) => void;
}

const statusColors: Record<string, string> = {
  created: "bg-slate-500",
  active: "bg-green-500",
  processing: "bg-blue-500",
  completed: "bg-emerald-500",
  failed: "bg-red-500",
  archived: "bg-gray-500",
};

const stageLabels: Record<string, string> = {
  initialization: "Initializing",
  data_acquisition: "Downloading",
  processing: "Processing",
  analysis: "Analyzing",
  reporting: "Reporting",
};

export default function ProjectCard({ project, selected, onSelect }: ProjectCardProps) {
  const navigate = useNavigate();
  const toggleFavorite = useToggleFavorite();

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    toggleFavorite.mutate(project.id);
  };

  const handleCardClick = () => {
    if (onSelect) {
      onSelect(project.id);
    } else {
      navigate(`/projects/${project.id}`);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    const parsed = new Date(dateStr);
    if (Number.isNaN(parsed.getTime())) return "Never";
    return parsed.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div
      onClick={handleCardClick}
      className={`
        relative bg-slate-800/50 border rounded-xl p-5 cursor-pointer
        transition-all duration-200 hover:bg-slate-700/50 hover:border-slate-600
        ${selected ? "border-primary-500 ring-2 ring-primary-500/30" : "border-slate-700/50"}
      `}
    >
      {/* Favorite Button */}
      <button
        onClick={handleFavoriteClick}
        className="absolute top-3 right-3 p-1 rounded-full hover:bg-slate-600/50 transition-colors"
      >
        <svg
          className={`w-5 h-5 ${project.favorite ? "text-yellow-400 fill-yellow-400" : "text-slate-400"}`}
          fill={project.favorite ? "currentColor" : "none"}
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
          />
        </svg>
      </button>

      {/* Status Badge */}
      <div className="flex items-center gap-2 mb-3">
        <span
          className={`w-2 h-2 rounded-full ${statusColors[project.status] || "bg-slate-500"}`}
        />
        <span className="text-xs text-slate-400 capitalize">{project.status}</span>
        {project.is_processing && (
          <span className="text-xs text-blue-400 ml-auto">Processing...</span>
        )}
      </div>

      {/* Project Name */}
      <h3 className="text-lg font-semibold text-white mb-1 truncate">{project.name}</h3>

      {/* Description */}
      {project.description && (
        <p className="text-sm text-slate-400 mb-3 line-clamp-2">{project.description}</p>
      )}

      {/* Progress Bar */}
      {project.progress > 0 && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>{stageLabels[project.current_stage || ""] || project.current_stage}</span>
            <span>{Math.round(project.progress)}%</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1.5">
            <div
              className="bg-primary-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${project.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Tags */}
      {parseTagArray(project.tags).length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {parseTagArray(project.tags)
            .slice(0, 3)
            .map((tag, i) => (
              <span
                key={i}
                className="px-2 py-0.5 text-xs bg-slate-700/50 text-slate-300 rounded"
              >
                {tag}
              </span>
            ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-slate-500 mt-auto pt-3 border-t border-slate-700/50">
        <span>Created {formatDate(project.created_at)}</span>
        <span>Opened {formatDate(project.last_opened_at)}</span>
      </div>
    </div>
  );
}
