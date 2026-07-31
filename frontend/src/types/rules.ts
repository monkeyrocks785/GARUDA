export interface Rule {
  id: string;
  name: string;
  description: string | null;
  rule_type: string;
  enabled: boolean;
  priority: string;
  project_id: string | null;
  mission_id: string | null;
  tags_json: string | null;
  created_by: string | null;
  last_evaluated_at: string | null;
  evaluation_count: number;
  alert_count: number;
  created_at: string | null;
  modified_at: string | null;
  conditions?: RuleCondition[];
  actions?: RuleAction[];
}

export interface RuleCondition {
  id: string;
  rule_id: string;
  group_index: number;
  parent_group_id: string | null;
  condition_type: string;
  field: string;
  operator: string;
  value_json: string | null;
  logical_operator: string | null;
  sort_order: number;
  created_at: string | null;
}

export interface RuleAction {
  id: string;
  rule_id: string;
  action_type: string;
  config_json: string | null;
  sort_order: number;
  created_at: string | null;
}

export interface Alert {
  id: string;
  rule_id: string | null;
  rule_name: string;
  rule_type: string;
  entity_id: string | null;
  entity_name: string | null;
  project_id: string | null;
  mission_id: string | null;
  priority: string;
  status: string;
  title: string;
  description: string | null;
  detail_json: string | null;
  geometry_json: string | null;
  centroid_x: number | null;
  centroid_y: number | null;
  assigned_to: string | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
  created_at: string | null;
  modified_at: string | null;
  history?: AlertHistoryEntry[];
}

export interface AlertHistoryEntry {
  id: string;
  alert_id: string;
  action: string;
  actor: string | null;
  notes: string | null;
  previous_status: string | null;
  new_status: string | null;
  created_at: string | null;
}

export interface RuleCreatePayload {
  name: string;
  description?: string;
  rule_type: string;
  enabled?: boolean;
  priority?: string;
  project_id?: string;
  mission_id?: string;
  tags?: string[];
  created_by?: string;
  conditions?: ConditionPayload[];
  actions?: ActionPayload[];
}

export interface ConditionPayload {
  condition_type: string;
  field: string;
  operator: string;
  value?: unknown;
  group_index?: number;
  parent_group_id?: string;
  logical_operator?: string;
  sort_order?: number;
}

export interface ActionPayload {
  action_type: string;
  config?: Record<string, unknown>;
  sort_order?: number;
}

export interface RulesConfig {
  rule_types: string[];
  condition_types: string[];
  logical_operators: string[];
  action_types: string[];
  alert_priorities: string[];
  alert_statuses: string[];
}

export interface AlertStats {
  total_alerts: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  by_rule_type: Record<string, number>;
  recent_alerts: Alert[];
}

export interface RuleStats {
  total_rules: number;
  enabled_rules: number;
  disabled_rules: number;
  rules_by_type: Record<string, number>;
  total_alerts: number;
  new_alerts: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
