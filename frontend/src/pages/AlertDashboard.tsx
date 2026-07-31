import { useState, useEffect, useCallback } from "react";
import { rulesApi } from "../services/rulesApi";
import type { Alert, AlertStats } from "../types/rules";
import { useToastStore } from "../store/useToastStore";
import { getErrorMessage } from "../utils/errorMessage";
import { formatDate } from "../utils/format";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import EmptyState from "../components/ui/EmptyState";

const STATUS_COLORS: Record<string, string> = {
  new: "bg-blue-500/20 text-blue-400",
  acknowledged: "bg-yellow-500/20 text-yellow-400",
  in_review: "bg-purple-500/20 text-purple-400",
  resolved: "bg-green-500/20 text-green-400",
  dismissed: "bg-slate-500/20 text-slate-400",
  archived: "bg-slate-600/20 text-slate-500",
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-slate-500",
  medium: "bg-yellow-500",
  high: "bg-orange-500",
  critical: "bg-red-500",
};

const PRIORITY_BG: Record<string, string> = {
  low: "border-l-slate-500",
  medium: "border-l-yellow-500",
  high: "border-l-orange-500",
  critical: "border-l-red-500",
};

// Action word -> actual backend alert status value
const STATUS_ACTIONS: Record<string, { label: string; status: string }[]> = {
  new: [
    { label: "Acknowledge", status: "acknowledged" },
    { label: "Dismiss", status: "dismissed" },
  ],
  acknowledged: [
    { label: "In Review", status: "in_review" },
    { label: "Dismiss", status: "dismissed" },
  ],
  in_review: [
    { label: "Resolve", status: "resolved" },
    { label: "Dismiss", status: "dismissed" },
  ],
  resolved: [{ label: "Archive", status: "archived" }],
  dismissed: [{ label: "Archive", status: "archived" }],
  archived: [],
};

export default function AlertDashboard() {
  const toast = useToastStore();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [actionNotes, setActionNotes] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const params: Record<string, unknown> = { page_size: 100 };
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;

      const [alertsRes, statsRes] = await Promise.all([
        rulesApi.listAlerts(params),
        rulesApi.getAlertStats(),
      ]);
      setAlerts(alertsRes.data.items);
      setStats(statsRes.data);
    } catch (err) {
      setLoadError(getErrorMessage(err, "Failed to load alerts"));
      console.error("Failed to load alerts", err);
    }
    setLoading(false);
  }, [statusFilter, priorityFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleAction(alertId: string, status: string, label: string) {
    try {
      await rulesApi.updateAlertStatus(alertId, {
        status,
        actor: "analyst",
        notes: actionNotes || undefined,
      });
      setActionNotes("");
      toast.success(`Alert ${label.toLowerCase()}`);
      await loadData();
      setSelectedAlert(null);
    } catch (err) {
      const msg = getErrorMessage(err, "Failed to update alert");
      toast.error(msg);
      console.error("Failed to update alert", err);
    }
  }

  if (loading && alerts.length === 0) {
    return (
      <div className="p-6">
        <LoadingState label="Loading alerts..." />
      </div>
    );
  }

  if (loadError && alerts.length === 0) {
    return (
      <div className="p-6">
        <ErrorState title="Failed to load alerts" message={loadError} onRetry={loadData} />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Alert Dashboard</h1>
        <p className="text-sm text-slate-400 mt-1">
          Monitor and manage intelligence alerts
        </p>
      </div>

      {loadError && alerts.length > 0 && (
        <div className="p-3 bg-red-500/10 border border-red-500/40 rounded-lg text-red-300 text-sm flex items-center justify-between">
          <span>{loadError}</span>
          <button onClick={loadData} className="text-red-200 underline text-xs hover:text-white">
            Retry
          </button>
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Object.entries(stats.by_status || {}).map(([status, count]) => (
            <div
              key={status}
              className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4"
            >
              <div className="text-2xl font-bold text-white">{count}</div>
              <div className="text-sm text-slate-400 capitalize">{status.replace("_", " ")}</div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-4 items-center">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-primary-500"
          aria-label="Filter by status"
        >
          <option value="">All Statuses</option>
          <option value="new">New</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="in_review">In Review</option>
          <option value="resolved">Resolved</option>
          <option value="dismissed">Dismissed</option>
        </select>
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-primary-500"
          aria-label="Filter by priority"
        >
          <option value="">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <span className="text-sm text-slate-500">
          {alerts.length} alert{alerts.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          {alerts.length === 0 ? (
            <EmptyState
              title={statusFilter || priorityFilter ? "No alerts match your filters" : "No alerts yet"}
              description={
                statusFilter || priorityFilter
                  ? "Try adjusting your filters."
                  : "Alerts generated by intelligence rules will appear here."
              }
            />
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.id}
                onClick={() => setSelectedAlert(alert)}
                className={`bg-slate-800/30 border-l-4 ${
                  PRIORITY_BG[alert.priority] || "border-l-slate-500"
                } border border-slate-700/50 rounded-r-xl p-4 hover:bg-slate-800/50 cursor-pointer transition-colors ${
                  selectedAlert?.id === alert.id ? "ring-2 ring-primary-500" : ""
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-white truncate">{alert.title}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[alert.status] || "bg-slate-500/20 text-slate-400"}`}>
                        {alert.status.replace("_", " ")}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-2 text-xs text-slate-500 flex-wrap">
                      <span>{alert.rule_name}</span>
                      {alert.entity_name && <span>Entity: {alert.entity_name}</span>}
                      <span>{formatDate(alert.created_at)}</span>
                      {alert.assigned_to && <span>Assigned: {alert.assigned_to}</span>}
                    </div>
                  </div>
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded-full text-white ml-2 ${
                      PRIORITY_COLORS[alert.priority] || "bg-slate-500"
                    }`}
                  >
                    {alert.priority}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 h-fit">
          {selectedAlert ? (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white">Alert Details</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-slate-400">Title:</span>
                  <p className="text-white">{selectedAlert.title}</p>
                </div>
                <div>
                  <span className="text-slate-400">Rule:</span>
                  <p className="text-white">{selectedAlert.rule_name}</p>
                </div>
                <div>
                  <span className="text-slate-400">Type:</span>
                  <p className="text-white capitalize">{selectedAlert.rule_type.replace("_", " ")}</p>
                </div>
                <div>
                  <span className="text-slate-400">Status:</span>
                  <p className="text-white capitalize">{selectedAlert.status.replace("_", " ")}</p>
                </div>
                <div>
                  <span className="text-slate-400">Priority:</span>
                  <p className="text-white capitalize">{selectedAlert.priority}</p>
                </div>
                <div>
                  <span className="text-slate-400">Entity:</span>
                  <p className="text-white">{selectedAlert.entity_name || "N/A"}</p>
                </div>
                <div>
                  <span className="text-slate-400">Created:</span>
                  <p className="text-white">{formatDate(selectedAlert.created_at)}</p>
                </div>
                {selectedAlert.assigned_to && (
                  <div>
                    <span className="text-slate-400">Assigned to:</span>
                    <p className="text-white">{selectedAlert.assigned_to}</p>
                  </div>
                )}
              </div>

              <textarea
                value={actionNotes}
                onChange={(e) => setActionNotes(e.target.value)}
                placeholder="Add notes..."
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:border-primary-500"
                rows={2}
              />

              <div className="flex flex-wrap gap-2">
                {(STATUS_ACTIONS[selectedAlert.status] || []).map((action) => (
                  <button
                    key={action.status}
                    onClick={() => handleAction(selectedAlert.id, action.status, action.label)}
                    className="px-3 py-1.5 text-xs font-medium bg-primary-600/20 text-primary-400 rounded-lg hover:bg-primary-600/30 transition-colors capitalize"
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              Select an alert to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
