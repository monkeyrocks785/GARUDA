import { useMissionStore } from "../store/useMissionStore";
import MissionList from "../components/missions/MissionList";
import MissionDetails from "../components/missions/MissionDetails";
import MissionTimeline from "../components/missions/MissionTimeline";
import CreateMission from "../components/missions/CreateMission";
import MissionStats from "../components/missions/MissionStats";
import Breadcrumbs from "../components/ui/Breadcrumbs";

export default function MissionManager() {
  const { view, setView } = useMissionStore();

  return (
    <div className="h-full flex flex-col bg-slate-900">
      <div className="px-4 py-2 border-b border-slate-700/50 shrink-0">
        <Breadcrumbs
          items={[
            { label: "Dashboard", to: "/" },
            { label: "Missions" },
          ]}
        />
      </div>
      <div className="flex flex-1 min-h-0">
      {/* Sidebar */}
      <div className="w-72 border-r border-slate-700/50 flex flex-col">
        <div className="p-3 border-b border-slate-700/50 flex items-center justify-between">
          <h1 className="text-lg font-bold text-white">Missions</h1>
          <div className="flex gap-1">
            <button
              onClick={() => setView("list")}
              className={`px-2 py-1 text-xs rounded ${view === "list" || view === "detail" ? "bg-primary-600 text-white" : "bg-slate-700/50 text-slate-400"}`}
            >
              Missions
            </button>
            <button
              onClick={() => setView("timeline")}
              className={`px-2 py-1 text-xs rounded ${view === "timeline" ? "bg-primary-600 text-white" : "bg-slate-700/50 text-slate-400"}`}
            >
              Timeline
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {view === "timeline" ? <div className="p-4 text-sm text-slate-400">Mission timeline is shown in the main area.</div> : <MissionList />}
        </div>
        {view !== "timeline" && <CreateMission />}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        {view === "timeline" ? (
          <MissionTimeline />
        ) : (
          <MissionDetails />
        )}
      </div>

      {/* Stats Panel */}
      <div className="w-48 border-l border-slate-700/50 bg-slate-800/30">
        <MissionStats />
      </div>
      </div>
    </div>
  );
}
