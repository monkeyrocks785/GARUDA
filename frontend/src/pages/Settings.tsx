import { useDetailedHealth } from "../hooks/useHealth";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import EmptyState from "../components/ui/EmptyState";

export default function Settings() {
  const { data: health, isLoading, isError, refetch } = useDetailedHealth();

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 mt-1">System and instance configuration</p>
      </div>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4">Instance Status</h3>
        {isLoading ? (
          <LoadingState compact label="Checking system status..." />
        ) : isError ? (
          <ErrorState
            compact
            title="Unable to reach the backend"
            message="Settings are managed by the backend server. Start the backend to view system status."
            onRetry={() => refetch()}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider">Status</p>
              <p className="text-white font-medium mt-1 capitalize">{health?.status || "unknown"}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider">Database</p>
              <p className="text-white font-medium mt-1 capitalize">{health?.database || "unknown"}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider">Last Checked</p>
              <p className="text-white font-medium mt-1">
                {health?.timestamp ? new Date(health.timestamp).toLocaleString() : "unknown"}
              </p>
            </div>
          </div>
        )}
      </div>

      <EmptyState
        title="Configuration pages are not available yet"
        description="Application configuration (data sources, models, storage) is managed through server environment variables and the backend API. No configuration API is currently exposed."
      />
    </div>
  );
}
