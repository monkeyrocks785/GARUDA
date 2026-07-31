import { useState, useEffect, useCallback } from "react";
import { rulesApi } from "../services/rulesApi";
import type { Rule, RulesConfig } from "../types/rules";
import { useToastStore } from "../store/useToastStore";
import { getErrorMessage } from "../utils/errorMessage";
import { formatDate } from "../utils/format";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import LoadingState from "../components/ui/LoadingState";
import ErrorState from "../components/ui/ErrorState";
import ConfirmDialog from "../components/ui/ConfirmDialog";

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-slate-500",
  medium: "bg-yellow-500",
  high: "bg-orange-500",
  critical: "bg-red-500",
};

const TYPE_COLORS: Record<string, string> = {
  entity: "text-blue-400",
  spatial: "text-green-400",
  temporal: "text-purple-400",
  growth: "text-cyan-400",
  relationship: "text-pink-400",
  attribute: "text-amber-400",
  pipeline_completion: "text-indigo-400",
  custom_composite: "text-rose-400",
};

const EMPTY_FORM = {
  name: "",
  description: "",
  rule_type: "entity",
  priority: "medium",
  project_id: "",
  enabled: true,
};

export default function RuleManager() {
  const toast = useToastStore();
  const [rules, setRules] = useState<Rule[]>([]);
  const [config, setConfig] = useState<RulesConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingRule, setEditingRule] = useState<Rule | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Rule | null>(null);
  const [filter, setFilter] = useState("");

  const [formData, setFormData] = useState({ ...EMPTY_FORM });

  const loadData = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [configRes, rulesRes] = await Promise.all([
        rulesApi.getConfig(),
        rulesApi.listRules({ page_size: 100 }),
      ]);
      setConfig(configRes.data);
      setRules(rulesRes.data.items);
    } catch (err) {
      setLoadError(getErrorMessage(err, "Failed to load rules"));
      console.error("Failed to load rules data", err);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      if (editingRule) {
        const res = await rulesApi.updateRule(editingRule.id, formData);
        setRules((prev) => prev.map((r) => (r.id === editingRule.id ? res.data : r)));
        toast.success("Rule updated");
      } else {
        const res = await rulesApi.createRule(formData);
        setRules((prev) => [res.data, ...prev]);
        toast.success("Rule created");
      }
      setShowForm(false);
      setEditingRule(null);
      resetForm();
    } catch (err) {
      const msg = getErrorMessage(err, "Failed to save rule");
      setFormError(msg);
      toast.error(msg);
      console.error("Failed to save rule", err);
    }
    setSaving(false);
  }

  async function handleToggleEnabled(rule: Rule) {
    try {
      if (rule.enabled) {
        await rulesApi.disableRule(rule.id);
      } else {
        await rulesApi.enableRule(rule.id);
      }
      toast.success(rule.enabled ? "Rule disabled" : "Rule enabled");
      await loadData();
    } catch (err) {
      const msg = getErrorMessage(err, "Failed to toggle rule");
      toast.error(msg);
      console.error("Failed to toggle rule", err);
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return;
    try {
      await rulesApi.deleteRule(deleteTarget.id);
      setRules((prev) => prev.filter((r) => r.id !== deleteTarget.id));
      toast.success("Rule deleted");
    } catch (err) {
      const msg = getErrorMessage(err, "Failed to delete rule");
      toast.error(msg);
      console.error("Failed to delete rule", err);
    }
    setDeleteTarget(null);
  }

  function handleEdit(rule: Rule) {
    setEditingRule(rule);
    setFormData({
      name: rule.name,
      description: rule.description || "",
      rule_type: rule.rule_type,
      priority: rule.priority,
      project_id: rule.project_id || "",
      enabled: rule.enabled,
    });
    setShowForm(true);
  }

  function resetForm() {
    setFormData({ ...EMPTY_FORM });
  }

  const filteredRules = filter
    ? rules.filter(
        (r) =>
          r.name.toLowerCase().includes(filter.toLowerCase()) ||
          r.rule_type.toLowerCase().includes(filter.toLowerCase()) ||
          r.priority.toLowerCase().includes(filter.toLowerCase())
      )
    : rules;

  if (loading) {
    return (
      <div className="p-6">
        <LoadingState label="Loading rules..." />
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="p-6">
        <ErrorState title="Failed to load rules" message={loadError} onRetry={loadData} />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Rule Manager</h1>
          <p className="text-sm text-slate-400 mt-1">
            Define and manage intelligence rules
          </p>
        </div>
        <Button
          onClick={() => {
            setEditingRule(null);
            resetForm();
            setFormError(null);
            setShowForm(true);
          }}
        >
          + New Rule
        </Button>
      </div>

      <div className="flex gap-4 items-center">
        <input
          type="text"
          placeholder="Search rules..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 flex-1 max-w-md focus:outline-none focus:border-primary-500"
        />
        <span className="text-sm text-slate-500">
          {filteredRules.length} rule{filteredRules.length !== 1 ? "s" : ""}
        </span>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 space-y-4"
        >
          <h3 className="text-lg font-semibold text-white">
            {editingRule ? "Edit Rule" : "Create Rule"}
          </h3>
          {formError && (
            <div className="p-3 bg-red-500/10 border border-red-500/40 rounded-lg text-red-300 text-sm">
              {formError}
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm text-slate-400" htmlFor="rule-name">Name *</label>
              <input
                id="rule-name"
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400" htmlFor="rule-type">Type</label>
              <select
                id="rule-type"
                value={formData.rule_type}
                onChange={(e) => setFormData({ ...formData, rule_type: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
              >
                {(config?.rule_types || ["entity", "spatial", "temporal"]).map((t) => (
                  <option key={t} value={t}>
                    {t.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400" htmlFor="rule-priority">Priority</label>
              <select
                id="rule-priority"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
              >
                {(config?.alert_priorities || ["low", "medium", "high", "critical"]).map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400" htmlFor="rule-project">Project ID (optional)</label>
              <input
                id="rule-project"
                type="text"
                value={formData.project_id}
                onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                placeholder="Leave blank for global rules"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400" htmlFor="rule-description">Description</label>
            <textarea
              id="rule-description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-primary-500"
              rows={2}
            />
          </div>
          <div className="flex gap-3 justify-end">
            <Button variant="ghost" type="button" onClick={() => { setShowForm(false); setEditingRule(null); }}>
              Cancel
            </Button>
            <Button type="submit" isLoading={saving}>
              {editingRule ? "Update" : "Create"}
            </Button>
          </div>
        </form>
      )}

      {filteredRules.length === 0 ? (
        <EmptyState
          title={filter ? "No rules match your filter" : "No rules defined yet"}
          description={
            filter
              ? "Try adjusting your search criteria."
              : "Create your first rule to start evaluating intelligence conditions and generating alerts."
          }
        />
      ) : (
        <div className="space-y-3">
          {filteredRules.map((rule) => (
            <div
              key={rule.id}
              className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-5 hover:border-slate-600 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-white">{rule.name}</h3>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${TYPE_COLORS[rule.rule_type] || "text-slate-400"} bg-slate-700/50`}>
                      {rule.rule_type.replace("_", " ")}
                    </span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full text-white ${PRIORITY_COLORS[rule.priority] || "bg-slate-500"}`}>
                      {rule.priority}
                    </span>
                  </div>
                  {rule.description && (
                    <p className="text-sm text-slate-400 mt-1">{rule.description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                    <span>Evaluations: {rule.evaluation_count || 0}</span>
                    <span>Alerts: {rule.alert_count || 0}</span>
                    {rule.last_evaluated_at && (
                      <span>Last: {formatDate(rule.last_evaluated_at)}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => handleToggleEnabled(rule)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                      rule.enabled
                        ? "bg-green-500/20 text-green-400 hover:bg-green-500/30"
                        : "bg-slate-600/20 text-slate-400 hover:bg-slate-600/30"
                    }`}
                  >
                    {rule.enabled ? "Enabled" : "Disabled"}
                  </button>
                  <Button variant="secondary" size="sm" onClick={() => handleEdit(rule)}>
                    Edit
                  </Button>
                  <Button variant="danger" size="sm" onClick={() => setDeleteTarget(rule)}>
                    Delete
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete rule?"
        message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
