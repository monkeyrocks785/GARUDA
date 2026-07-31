"""Intelligence Rules & Alert Engine API.

Endpoints for creating, updating, deleting, and executing intelligence rules,
and for managing generated alerts.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from rules_engine.config import (
    ACTION_TYPES,
    ALERT_PRIORITIES,
    ALERT_STATUSES,
    CONDITION_TYPES,
    LOGICAL_OPERATORS,
    RULE_TYPES,
)
from rules_engine.database.models import Alert, AlertHistory
from rules_engine.services.alert_service import AlertService
from rules_engine.services.rule_service import RuleService

logger = logging.getLogger("garuda.rules.api")

router = APIRouter(prefix="/rules", tags=["Rules & Alert Engine"])


class ConditionSchema(BaseModel):
    condition_type: str = Field(..., description="Type of condition")
    field: str = Field(..., description="Field or value to evaluate")
    operator: str = Field(..., description="Comparison operator")
    value: object | None = None
    group_index: int = 0
    parent_group_id: str | None = None
    logical_operator: str | None = None
    sort_order: int = 0


class ActionSchema(BaseModel):
    action_type: str = Field(..., description="Action to take when rule fires")
    config: dict | None = None
    sort_order: int = 0


class RuleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    rule_type: str = Field(..., description="Type of rule")
    enabled: bool = True
    priority: str = "medium"
    project_id: str | None = None
    mission_id: str | None = None
    tags: list[str] | None = None
    created_by: str | None = None
    conditions: list[ConditionSchema] | None = None
    actions: list[ActionSchema] | None = None


class RuleUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    rule_type: str | None = None
    enabled: bool | None = None
    priority: str | None = None
    project_id: str | None = None
    mission_id: str | None = None
    tags: list[str] | None = None
    conditions: list[ConditionSchema] | None = None
    actions: list[ActionSchema] | None = None


class AlertStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="New alert status")
    actor: str | None = None
    notes: str | None = None


class AlertAssignRequest(BaseModel):
    assigned_to: str = Field(..., description="Analyst to assign the alert to")
    actor: str | None = None


class RuleExecuteRequest(BaseModel):
    project_id: str = Field(..., description="Project to evaluate the rule against")


# ── Config Endpoint ─────────────────────────────────────────────────────────

@router.get("/config")
def get_rules_config():
    """Get Rules & Alert Engine configuration."""
    return {
        "rule_types": RULE_TYPES,
        "condition_types": CONDITION_TYPES,
        "logical_operators": LOGICAL_OPERATORS,
        "action_types": ACTION_TYPES,
        "alert_priorities": ALERT_PRIORITIES,
        "alert_statuses": ALERT_STATUSES,
    }


# ── Rule Endpoints ──────────────────────────────────────────────────────────

@router.post("/rules", status_code=201)
def create_rule(data: RuleCreateRequest, db: Session = Depends(get_db)):
    """Create a new intelligence rule."""
    try:
        rule = RuleService.create_rule(
            db=db,
            name=data.name,
            description=data.description,
            rule_type=data.rule_type,
            enabled=data.enabled,
            priority=data.priority,
            project_id=data.project_id,
            mission_id=data.mission_id,
            tags=data.tags,
            created_by=data.created_by,
            conditions=[c.model_dump() for c in data.conditions] if data.conditions else None,
            actions=[a.model_dump() for a in data.actions] if data.actions else None,
        )
        return RuleService.get_rule_with_details(db, rule.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules")
def list_rules(
    project_id: str | None = Query(None),
    rule_type: str | None = Query(None),
    enabled: bool | None = Query(None),
    mission_id: str | None = Query(None),
    priority: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List intelligence rules with optional filters."""
    items, total = RuleService.list_rules(
        db, project_id=project_id, rule_type=rule_type,
        enabled=enabled, mission_id=mission_id, priority=priority,
        page=page, page_size=page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/rules/{rule_id}")
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    """Get a specific rule with its conditions and actions."""
    try:
        return RuleService.get_rule_with_details(db, rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/rules/{rule_id}")
def update_rule(rule_id: str, data: RuleUpdateRequest, db: Session = Depends(get_db)):
    """Update an existing rule."""
    try:
        rule = RuleService.update_rule(
            db=db,
            rule_id=rule_id,
            name=data.name,
            description=data.description,
            rule_type=data.rule_type,
            enabled=data.enabled,
            priority=data.priority,
            project_id=data.project_id,
            mission_id=data.mission_id,
            tags=data.tags,
            conditions=[c.model_dump() for c in data.conditions] if data.conditions else None,
            actions=[a.model_dump() for a in data.actions] if data.actions else None,
        )
        return RuleService.get_rule_with_details(db, rule.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    """Delete a rule and its associated conditions and actions."""
    try:
        RuleService.delete_rule(db, rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rules/{rule_id}/enable")
def enable_rule(rule_id: str, db: Session = Depends(get_db)):
    """Enable a rule."""
    try:
        rule = RuleService.set_rule_enabled(db, rule_id, True)
        return {"id": rule.id, "enabled": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rules/{rule_id}/disable")
def disable_rule(rule_id: str, db: Session = Depends(get_db)):
    """Disable a rule."""
    try:
        rule = RuleService.set_rule_enabled(db, rule_id, False)
        return {"id": rule.id, "enabled": False}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rules/{rule_id}/execute")
def execute_rule(rule_id: str, data: RuleExecuteRequest, db: Session = Depends(get_db)):
    """Execute a rule against a project to generate alerts."""
    try:
        return RuleService.execute_rule(db, rule_id, data.project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Alert Endpoints ─────────────────────────────────────────────────────────

@router.get("/alerts")
def list_alerts(
    project_id: str | None = Query(None),
    rule_id: str | None = Query(None),
    rule_type: str | None = Query(None),
    priority: str | None = Query(None),
    status: str | None = Query(None),
    entity_id: str | None = Query(None),
    assigned_to: str | None = Query(None),
    mission_id: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List alerts with optional filters."""
    items, total = AlertService.list_alerts(
        db, project_id=project_id, rule_id=rule_id, rule_type=rule_type,
        priority=priority, status=status, entity_id=entity_id,
        assigned_to=assigned_to, mission_id=mission_id,
        page=page, page_size=page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/alerts/stats")
def get_alert_stats(
    project_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get alert statistics."""
    return AlertService.get_alert_stats(db, project_id=project_id)


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    """Get a specific alert with its history."""
    try:
        return AlertService.get_alert_with_history(db, alert_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/alerts/{alert_id}/status")
def update_alert_status(
    alert_id: str,
    data: AlertStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update alert status (acknowledge, resolve, etc.)."""
    try:
        alert = AlertService.update_alert_status(
            db, alert_id, data.status, data.actor, data.notes
        )
        return alert.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    actor: str | None = Query(None),
    notes: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Acknowledge an alert."""
    try:
        alert = AlertService.acknowledge_alert(db, alert_id, actor, notes)
        return alert.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: str,
    actor: str | None = Query(None),
    notes: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Resolve an alert."""
    try:
        alert = AlertService.resolve_alert(db, alert_id, actor, notes)
        return alert.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/assign")
def assign_alert(
    alert_id: str,
    data: AlertAssignRequest,
    db: Session = Depends(get_db),
):
    """Assign an alert to an analyst."""
    try:
        alert = AlertService.assign_alert(db, alert_id, data.assigned_to, data.actor)
        return alert.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/alerts/{alert_id}/history")
def get_alert_history(alert_id: str, db: Session = Depends(get_db)):
    """Get the full history of an alert."""
    history = (
        db.query(AlertHistory)
        .filter(AlertHistory.alert_id == alert_id)
        .order_by(AlertHistory.created_at.asc())
        .all()
    )
    return {"items": [h.to_dict() for h in history]}


# ── Statistics Endpoints ────────────────────────────────────────────────────

@router.get("/stats")
def get_rule_stats(db: Session = Depends(get_db)):
    """Get overall rules and alerts statistics."""
    return RuleService.get_rule_stats(db)
