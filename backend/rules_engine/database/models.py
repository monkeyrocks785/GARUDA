"""Database models for the Intelligence Rules & Alert Engine.

Stores rule definitions, conditions, actions, generated alerts, and alert history.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class Rule(Base):
    """A user-defined intelligence rule that triggers alerts."""

    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    mission_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    evaluation_count: Mapped[int] = mapped_column(Integer, default=0)
    alert_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type,
            "enabled": self.enabled,
            "priority": self.priority,
            "project_id": self.project_id,
            "mission_id": self.mission_id,
            "tags_json": self.tags_json,
            "created_by": self.created_by,
            "last_evaluated_at": self.last_evaluated_at.isoformat()
                if self.last_evaluated_at else None,
            "evaluation_count": self.evaluation_count,
            "alert_count": self.alert_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }


class RuleCondition(Base):
    """A single condition within a rule, linked by logical operators."""

    __tablename__ = "rule_conditions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    rule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rules.id", ondelete="CASCADE"), index=True
    )
    group_index: Mapped[int] = mapped_column(Integer, default=0)
    parent_group_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    condition_type: Mapped[str] = mapped_column(String(50))
    field: Mapped[str] = mapped_column(String(255))
    operator: Mapped[str] = mapped_column(String(50))
    value_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    logical_operator: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "group_index": self.group_index,
            "parent_group_id": self.parent_group_id,
            "condition_type": self.condition_type,
            "field": self.field,
            "operator": self.operator,
            "value_json": self.value_json,
            "logical_operator": self.logical_operator,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RuleAction(Base):
    """An action to take when a rule's conditions are all satisfied."""

    __tablename__ = "rule_actions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    rule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("rules.id", ondelete="CASCADE"), index=True
    )
    action_type: Mapped[str] = mapped_column(String(50))
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "action_type": self.action_type,
            "config_json": self.config_json,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Alert(Base):
    """An alert generated when a rule's conditions are met."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    rule_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("rules.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rule_name: Mapped[str] = mapped_column(String(255))
    rule_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    entity_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    mission_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True)
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    geometry_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    centroid_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    centroid_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "rule_type": self.rule_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "project_id": self.project_id,
            "mission_id": self.mission_id,
            "priority": self.priority,
            "status": self.status,
            "title": self.title,
            "description": self.description,
            "detail_json": self.detail_json,
            "geometry_json": self.geometry_json,
            "centroid_x": self.centroid_x,
            "centroid_y": self.centroid_y,
            "assigned_to": self.assigned_to,
            "acknowledged_at": self.acknowledged_at.isoformat()
                if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat()
                if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }


class AlertHistory(Base):
    """Audit trail of alert lifecycle events (acknowledge, resolve, etc.)."""

    __tablename__ = "alert_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    alert_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("alerts.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[str] = mapped_column(String(50), index=True)
    actor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "action": self.action,
            "actor": self.actor,
            "notes": self.notes,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
