"""Rule CRUD Service.

Manages creation, updating, deletion, and execution of intelligence rules.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from rules_engine.config import RULE_TYPES
from rules_engine.database.models import (
    Alert,
    AlertHistory,
    Rule,
    RuleAction,
    RuleCondition,
)
from rules_engine.services.evaluation_service import EvaluationService

logger = logging.getLogger("garuda.rules.service")


class RuleService:
    """Service for managing intelligence rules."""

    @staticmethod
    def create_rule(
        db: Session,
        name: str,
        rule_type: str,
        description: str | None = None,
        enabled: bool = True,
        priority: str = "medium",
        project_id: str | None = None,
        mission_id: str | None = None,
        tags: list[str] | None = None,
        created_by: str | None = None,
        conditions: list[dict] | None = None,
        actions: list[dict] | None = None,
    ) -> Rule:
        if rule_type not in RULE_TYPES:
            raise ValueError(f"Invalid rule type: {rule_type}. Must be one of {RULE_TYPES}")

        rule = Rule(
            name=name,
            description=description,
            rule_type=rule_type,
            enabled=enabled,
            priority=priority,
            project_id=project_id,
            mission_id=mission_id,
            tags_json=json.dumps(tags) if tags else None,
            created_by=created_by,
        )
        db.add(rule)
        db.flush()

        if conditions:
            for i, c in enumerate(conditions):
                rc = RuleCondition(
                    rule_id=rule.id,
                    group_index=c.get("group_index", 0),
                    parent_group_id=c.get("parent_group_id"),
                    condition_type=c["condition_type"],
                    field=c["field"],
                    operator=c["operator"],
                    value_json=json.dumps(c.get("value")) if "value" in c else None,
                    logical_operator=c.get("logical_operator"),
                    sort_order=c.get("sort_order", i),
                )
                db.add(rc)

        if actions:
            for i, a in enumerate(actions):
                ra = RuleAction(
                    rule_id=rule.id,
                    action_type=a["action_type"],
                    config_json=json.dumps(a.get("config", {})) if "config" in a else None,
                    sort_order=a.get("sort_order", i),
                )
                db.add(ra)

        db.commit()
        db.refresh(rule)
        logger.info(f"Rule created: {rule.id} ({name})")
        return rule

    @staticmethod
    def update_rule(
        db: Session,
        rule_id: str,
        name: str | None = None,
        description: str | None = None,
        rule_type: str | None = None,
        enabled: bool | None = None,
        priority: str | None = None,
        project_id: str | None = None,
        mission_id: str | None = None,
        tags: list[str] | None = None,
        conditions: list[dict] | None = None,
        actions: list[dict] | None = None,
    ) -> Rule:
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")

        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if rule_type is not None:
            if rule_type not in RULE_TYPES:
                raise ValueError(f"Invalid rule type: {rule_type}")
            rule.rule_type = rule_type
        if enabled is not None:
            rule.enabled = enabled
        if priority is not None:
            rule.priority = priority
        if project_id is not None:
            rule.project_id = project_id
        if mission_id is not None:
            rule.mission_id = mission_id
        if tags is not None:
            rule.tags_json = json.dumps(tags)

        if conditions is not None:
            db.query(RuleCondition).filter(RuleCondition.rule_id == rule_id).delete()
            for i, c in enumerate(conditions):
                rc = RuleCondition(
                    rule_id=rule.id,
                    group_index=c.get("group_index", 0),
                    parent_group_id=c.get("parent_group_id"),
                    condition_type=c["condition_type"],
                    field=c["field"],
                    operator=c["operator"],
                    value_json=json.dumps(c.get("value")) if "value" in c else None,
                    logical_operator=c.get("logical_operator"),
                    sort_order=c.get("sort_order", i),
                )
                db.add(rc)

        if actions is not None:
            db.query(RuleAction).filter(RuleAction.rule_id == rule_id).delete()
            for i, a in enumerate(actions):
                ra = RuleAction(
                    rule_id=rule.id,
                    action_type=a["action_type"],
                    config_json=json.dumps(a.get("config", {})) if "config" in a else None,
                    sort_order=a.get("sort_order", i),
                )
                db.add(ra)

        db.commit()
        db.refresh(rule)
        logger.info(f"Rule updated: {rule.id}")
        return rule

    @staticmethod
    def delete_rule(db: Session, rule_id: str) -> None:
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")
        db.delete(rule)
        db.commit()
        logger.info(f"Rule deleted: {rule_id}")

    @staticmethod
    def get_rule(db: Session, rule_id: str) -> Rule | None:
        return db.query(Rule).filter(Rule.id == rule_id).first()

    @staticmethod
    def get_rule_with_details(db: Session, rule_id: str) -> dict:
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")

        conditions = (
            db.query(RuleCondition)
            .filter(RuleCondition.rule_id == rule_id)
            .order_by(RuleCondition.sort_order.asc())
            .all()
        )
        actions = (
            db.query(RuleAction)
            .filter(RuleAction.rule_id == rule_id)
            .order_by(RuleAction.sort_order.asc())
            .all()
        )

        return {
            **rule.to_dict(),
            "conditions": [c.to_dict() for c in conditions],
            "actions": [a.to_dict() for a in actions],
        }

    @staticmethod
    def list_rules(
        db: Session,
        project_id: str | None = None,
        rule_type: str | None = None,
        enabled: bool | None = None,
        mission_id: str | None = None,
        priority: str | None = None,
        page: int = 0,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        q = db.query(Rule)
        if project_id is not None:
            q = q.filter(Rule.project_id == project_id)
        if rule_type is not None:
            q = q.filter(Rule.rule_type == rule_type)
        if enabled is not None:
            q = q.filter(Rule.enabled == enabled)
        if mission_id is not None:
            q = q.filter(Rule.mission_id == mission_id)
        if priority is not None:
            q = q.filter(Rule.priority == priority)

        total = q.count()
        items = q.order_by(Rule.modified_at.desc()).offset(page * page_size).limit(page_size).all()
        return [r.to_dict() for r in items], total

    @staticmethod
    def set_rule_enabled(db: Session, rule_id: str, enabled: bool) -> Rule:
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")
        rule.enabled = enabled
        db.commit()
        db.refresh(rule)
        logger.info(f"Rule {'enabled' if enabled else 'disabled'}: {rule_id}")
        return rule

    @staticmethod
    def execute_rule(db: Session, rule_id: str, project_id: str | None = None) -> dict[str, Any]:
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")
        if not rule.enabled:
            raise ValueError(f"Rule is disabled: {rule_id}")

        start = time.monotonic()

        pid = project_id or rule.project_id
        if not pid:
            raise ValueError("No project_id specified for rule execution")

        alerts_generated = EvaluationService.evaluate_rule_for_project(db, rule, pid)

        rule.last_evaluated_at = datetime.now(timezone.utc)
        rule.evaluation_count = (rule.evaluation_count or 0) + 1
        rule.alert_count = (rule.alert_count or 0) + len(alerts_generated)

        created_alerts = []
        for alert_data in alerts_generated:
            alert = Alert(
                rule_id=rule.id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                entity_id=alert_data.get("entity_id"),
                entity_name=alert_data.get("entity_name"),
                project_id=pid,
                priority=rule.priority,
                status="new",
                title=f"Rule triggered: {rule.name} on {alert_data.get('entity_name', 'unknown')}",
                detail_json=json.dumps(alert_data),
            )
            db.add(alert)
            db.flush()

            ah = AlertHistory(
                alert_id=alert.id,
                action="created",
                new_status="new",
            )
            db.add(ah)
            created_alerts.append(alert.to_dict())

        db.commit()

        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            f"Rule {rule.name} ({rule.id}) evaluated {len(alerts_generated)} matches "
            f"in {elapsed:.0f}ms, generated {len(created_alerts)} alerts"
        )

        return {
            "rule_id": rule_id,
            "rule_name": rule.name,
            "evaluated": True,
            "matches": len(alerts_generated),
            "alerts_generated": len(created_alerts),
            "alerts": created_alerts,
            "execution_time_ms": round(elapsed, 2),
        }

    @staticmethod
    def get_rule_stats(db: Session) -> dict[str, Any]:
        total = db.query(Rule).count()
        enabled = db.query(Rule).filter(Rule.enabled == True).count()
        by_type = {}
        for rt in RULE_TYPES:
            cnt = db.query(Rule).filter(Rule.rule_type == rt).count()
            if cnt > 0:
                by_type[rt] = cnt
        total_alerts = db.query(Alert).count()
        new_alerts = db.query(Alert).filter(Alert.status == "new").count()

        return {
            "total_rules": total,
            "enabled_rules": enabled,
            "disabled_rules": total - enabled,
            "rules_by_type": by_type,
            "total_alerts": total_alerts,
            "new_alerts": new_alerts,
        }
