"""Event Service.

Manages events that happen to entities in the knowledge graph.
"""

import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from knowledge_engine.config import DEFAULT_PAGE_SIZE, EVENT_TYPES, MAX_PAGE_SIZE
from knowledge_engine.database.models import Entity, EntityEvent

logger = logging.getLogger("garuda.knowledge.event_service")


class EventService:
    """CRUD operations for entity events."""

    @staticmethod
    def create_event(
        db: Session,
        entity_id: str,
        event_type: str,
        description: str | None = None,
        attributes: dict | None = None,
        geometry_json: str | None = None,
        confidence: float = 1.0,
        source_id: str | None = None,
        source_type: str | None = None,
        analyst_notes: str | None = None,
        event_time: datetime | None = None,
    ) -> EntityEvent:
        """Create an event for an entity."""
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Invalid event type: {event_type}. Must be one of {EVENT_TYPES}")

        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if entity is None:
            raise ValueError(f"Entity not found: {entity_id}")

        event = EntityEvent(
            entity_id=entity_id,
            event_type=event_type,
            description=description,
            attributes_json=json.dumps(attributes) if attributes else None,
            geometry_json=geometry_json,
            confidence=confidence,
            source_id=source_id,
            source_type=source_type,
            analyst_notes=analyst_notes,
            event_time=event_time or datetime.utcnow(),
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(f"Created event for entity {entity.name}: {event_type}")
        return event

    @staticmethod
    def get_event(db: Session, event_id: str) -> EntityEvent | None:
        """Get an event by ID."""
        return db.query(EntityEvent).filter(EntityEvent.id == event_id).first()

    @staticmethod
    def list_entity_events(
        db: Session,
        entity_id: str,
        event_type: str | None = None,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[EntityEvent], int]:
        """List events for an entity."""
        q = db.query(EntityEvent).filter(EntityEvent.entity_id == entity_id)
        if event_type:
            q = q.filter(EntityEvent.event_type == event_type)
        total = q.count()
        events = (
            q.order_by(EntityEvent.event_time.desc())
            .offset(page * min(page_size, MAX_PAGE_SIZE))
            .limit(min(page_size, MAX_PAGE_SIZE))
            .all()
        )
        return events, total

    @staticmethod
    def update_event(
        db: Session,
        event_id: str,
        description: str | None = None,
        attributes: dict | None = None,
        analyst_notes: str | None = None,
    ) -> EntityEvent | None:
        """Update an event."""
        event = db.query(EntityEvent).filter(EntityEvent.id == event_id).first()
        if event is None:
            return None

        if description is not None:
            event.description = description
        if attributes is not None:
            event.attributes_json = json.dumps(attributes)
        if analyst_notes is not None:
            event.analyst_notes = analyst_notes

        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def delete_event(db: Session, event_id: str) -> bool:
        """Delete an event."""
        event = db.query(EntityEvent).filter(EntityEvent.id == event_id).first()
        if event is None:
            return False
        db.delete(event)
        db.commit()
        return True

    @staticmethod
    def get_project_events(
        db: Session,
        project_id: str,
        event_type: str | None = None,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[dict], int]:
        """List all events for a project."""
        q = (
            db.query(EntityEvent)
            .join(Entity, EntityEvent.entity_id == Entity.id)
            .filter(Entity.project_id == project_id)
        )
        if event_type:
            q = q.filter(EntityEvent.event_type == event_type)
        total = q.count()
        events = (
            q.order_by(EntityEvent.event_time.desc())
            .offset(page * min(page_size, MAX_PAGE_SIZE))
            .limit(min(page_size, MAX_PAGE_SIZE))
            .all()
        )

        results = []
        for ev in events:
            entity = db.query(Entity).filter(Entity.id == ev.entity_id).first()
            d = ev.to_dict()
            d["entity_name"] = entity.name if entity else None
            d["entity_type"] = entity.entity_type if entity else None
            results.append(d)

        return results, total
