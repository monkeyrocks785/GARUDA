"""History Service.

Maintains a complete audit trail of all entity changes.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from knowledge_engine.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from knowledge_engine.database.models import EntityHistory

logger = logging.getLogger("garuda.knowledge.history_service")


class HistoryService:
    """Manages entity change history."""

    @staticmethod
    def record_change(
        db: Session,
        entity_id: str,
        change_type: str,
        field_name: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        change_summary: str | None = None,
        changed_by: str | None = None,
        source_id: str | None = None,
        source_type: str | None = None,
    ) -> EntityHistory:
        """Record a change to an entity."""
        entry = EntityHistory(
            entity_id=entity_id,
            change_type=change_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            change_summary=change_summary,
            changed_by=changed_by,
            source_id=source_id,
            source_type=source_type,
        )
        db.add(entry)
        db.commit()
        return entry

    @staticmethod
    def get_entity_history(
        db: Session,
        entity_id: str,
        change_type: str | None = None,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[EntityHistory], int]:
        """Get history for an entity."""
        q = db.query(EntityHistory).filter(EntityHistory.entity_id == entity_id)
        if change_type:
            q = q.filter(EntityHistory.change_type == change_type)
        total = q.count()
        entries = (
            q.order_by(EntityHistory.created_at.desc())
            .offset(page * min(page_size, MAX_PAGE_SIZE))
            .limit(min(page_size, MAX_PAGE_SIZE))
            .all()
        )
        return entries, total

    @staticmethod
    def get_history_summary(db: Session, entity_id: str) -> dict:
        """Get a summary of history for an entity."""
        entries = db.query(EntityHistory).filter(
            EntityHistory.entity_id == entity_id
        ).all()

        change_counts: dict[str, int] = {}
        for entry in entries:
            change_counts[entry.change_type] = change_counts.get(entry.change_type, 0) + 1

        first_entry = (
            db.query(EntityHistory)
            .filter(EntityHistory.entity_id == entity_id)
            .order_by(EntityHistory.created_at.asc())
            .first()
        )
        last_entry = (
            db.query(EntityHistory)
            .filter(EntityHistory.entity_id == entity_id)
            .order_by(EntityHistory.created_at.desc())
            .first()
        )

        return {
            "total_changes": len(entries),
            "change_counts": change_counts,
            "first_change_at": first_entry.created_at.isoformat() if first_entry else None,
            "last_change_at": last_entry.created_at.isoformat() if last_entry else None,
        }
