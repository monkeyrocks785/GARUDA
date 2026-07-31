import api from "./api";
import type {
  Rule,
  Alert,
  RuleCreatePayload,
  RulesConfig,
  AlertStats,
  RuleStats,
  PaginatedResponse,
  AlertHistoryEntry,
} from "../types/rules";

export const rulesApi = {
  getConfig: () => api.get<RulesConfig>("/rules/config"),

  createRule: (data: RuleCreatePayload) =>
    api.post<Rule>("/rules/rules", data),

  listRules: (params?: {
    project_id?: string;
    rule_type?: string;
    enabled?: boolean;
    mission_id?: string;
    priority?: string;
    page?: number;
    page_size?: number;
  }) => api.get<PaginatedResponse<Rule>>("/rules/rules", { params }),

  getRule: (id: string) => api.get<Rule>(`/rules/rules/${id}`),

  updateRule: (id: string, data: Partial<RuleCreatePayload>) =>
    api.put<Rule>(`/rules/rules/${id}`, data),

  deleteRule: (id: string) => api.delete(`/rules/rules/${id}`),

  enableRule: (id: string) =>
    api.post<{ id: string; enabled: boolean }>(`/rules/rules/${id}/enable`),

  disableRule: (id: string) =>
    api.post<{ id: string; enabled: boolean }>(`/rules/rules/${id}/disable`),

  executeRule: (id: string, projectId: string) =>
    api.post(`/rules/rules/${id}/execute`, { project_id: projectId }),

  listAlerts: (params?: {
    project_id?: string;
    rule_id?: string;
    rule_type?: string;
    priority?: string;
    status?: string;
    entity_id?: string;
    assigned_to?: string;
    mission_id?: string;
    page?: number;
    page_size?: number;
  }) => api.get<PaginatedResponse<Alert>>("/rules/alerts", { params }),

  getAlert: (id: string) => api.get<Alert>(`/rules/alerts/${id}`),

  updateAlertStatus: (id: string, data: {
    status: string;
    actor?: string;
    notes?: string;
  }) => api.patch<Alert>(`/rules/alerts/${id}/status`, data),

  acknowledgeAlert: (id: string, actor?: string, notes?: string) =>
    api.post<Alert>(`/rules/alerts/${id}/acknowledge`, null, {
      params: { actor, notes },
    }),

  resolveAlert: (id: string, actor?: string, notes?: string) =>
    api.post<Alert>(`/rules/alerts/${id}/resolve`, null, {
      params: { actor, notes },
    }),

  assignAlert: (id: string, assignedTo: string, actor?: string) =>
    api.post<Alert>(`/rules/alerts/${id}/assign`, {
      assigned_to: assignedTo,
      actor,
    }),

  getAlertHistory: (id: string) =>
    api.get<{ items: AlertHistoryEntry[] }>(`/rules/alerts/${id}/history`),

  getAlertStats: (projectId?: string) =>
    api.get<AlertStats>("/rules/alerts/stats", {
      params: projectId ? { project_id: projectId } : undefined,
    }),

  getRuleStats: () => api.get<RuleStats>("/rules/stats"),
};
