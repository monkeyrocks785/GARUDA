"""Configuration constants for the Intelligence Rules & Alert Engine."""

RULE_TYPES = [
    "entity",
    "spatial",
    "temporal",
    "growth",
    "relationship",
    "attribute",
    "pipeline_completion",
    "custom_composite",
]

CONDITION_TYPES = [
    "equals",
    "not_equals",
    "greater_than",
    "less_than",
    "between",
    "contains",
    "starts_with",
    "ends_with",
    "within_distance",
    "inside_aoi",
    "intersects",
    "touches",
    "first_observed",
    "last_observed",
    "observation_count",
    "growth_rate",
    "forecast_value",
    "confidence_score",
]

LOGICAL_OPERATORS = ["AND", "OR", "NOT"]

ACTION_TYPES = [
    "generate_alert",
    "create_notification",
    "create_task",
    "add_analyst_note",
    "highlight_on_map",
    "export_report",
    "trigger_pipeline",
    "mark_entity",
    "archive_alert",
]

ALERT_PRIORITIES = ["low", "medium", "high", "critical"]

ALERT_STATUSES = [
    "new",
    "acknowledged",
    "in_review",
    "resolved",
    "dismissed",
    "archived",
]

RULE_EVALUATION_EVENTS = [
    "rule_created",
    "rule_updated",
    "rule_deleted",
    "rule_enabled",
    "rule_disabled",
    "rule_executed",
    "alert_generated",
    "alert_acknowledged",
    "alert_resolved",
]

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
