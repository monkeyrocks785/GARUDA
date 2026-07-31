"""Intelligence Rules & Alert Engine.

Allows analysts to define configurable intelligence rules that evaluate
observations, entities, relationships, temporal trends, and analytics.
Generates alerts for analyst review — no autonomous decisions.
"""

from rules_engine.services.rule_service import RuleService
from rules_engine.services.alert_service import AlertService
from rules_engine.services.evaluation_service import EvaluationService

__all__ = [
    "RuleService",
    "AlertService",
    "EvaluationService",
]
