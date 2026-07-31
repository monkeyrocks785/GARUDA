import { useLocation, useParams } from "react-router-dom";
import { useHealth } from "../hooks/useHealth";

function getPageTitle(pathname: string): string {
  if (pathname === "/") return "Dashboard";
  if (pathname === "/projects") return "Projects";
  if (pathname === "/missions") return "Missions";
  if (pathname === "/timelines") return "Timelines";
  if (pathname === "/rules") return "Rules";
  if (pathname === "/alerts") return "Alerts";
  if (pathname === "/settings") return "Settings";
  if (pathname === "/about") return "About";

  if (pathname.startsWith("/projects/")) {
    const segments = pathname.split("/").filter(Boolean);
    if (segments.length === 2) return "Project";
    if (segments[2] === "map") return "GIS Workspace";
    if (segments[2] === "datasets") return "Datasets";
    if (segments[2] === "assets") return "Assets";
    if (segments[2] === "pipelines") return "Pipelines";
    if (segments[2] === "queries") return "Query Builder";
    return "Project";
  }

  return "GARUDA";
}

export default function TopNav() {
  const location = useLocation();
  const params = useParams();
  const { data: health, isLoading } = useHealth();
  const title = getPageTitle(location.pathname);

  const isOnline = health?.status === "ok" || health?.status === "healthy";

  return (
    <header className="h-16 bg-garuda-dark border-b border-slate-700/50 flex items-center justify-between px-6 shrink-0">
      <div>
        <h2 className="text-lg font-semibold text-white">{title}</h2>
        {params.id && (
          <p className="text-[11px] text-slate-500 font-mono">Project ID: {params.id}</p>
        )}
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          {isLoading ? (
            <span className="w-2 h-2 rounded-full bg-slate-500 animate-pulse" />
          ) : (
            <span className={`w-2 h-2 rounded-full ${isOnline ? "bg-green-500" : "bg-red-500"}`} />
          )}
          <span>{isOnline ? "System Online" : "Backend Unavailable"}</span>
        </div>
        <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
          <span className="text-sm font-medium text-slate-300">U</span>
        </div>
      </div>
    </header>
  );
}
