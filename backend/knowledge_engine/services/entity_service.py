"""Entity CRUD Service.

Manages creation, retrieval, update, and deletion of persistent
real-world entities in the knowledge graph.
"""

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from knowledge_engine.config import (
    DEFAULT_CONFIDENCE,
    DEFAULT_PAGE_SIZE,
    ENTITY_STATUSES,
    ENTITY_TYPES,
    MAX_PAGE_SIZE,
)
from knowledge_engine.database.models import (
    Entity,
    EntityEvent,
    EntityHistory,
    EntityObservation,
    EntityRelationship,
)
from knowledge_engine.services.history_service import HistoryService

logger = logging.getLogger("garuda.knowledge.entity_service")


class EntityService:
    """CRUD operations for entities."""

    @staticmethod
    def create_entity(
        db: Session,
        project_id: str,
        entity_type: str,
        name: str,
        description: str | None = None,
        confidence: float = DEFAULT_CONFIDENCE,
        geometry_json: str | None = None,
        bbox: list[float] | None = None,
        centroid: list[float] | None = None,
        attributes: dict | None = None,
        tags: list[str] | None = None,
        analyst_notes: str | None = None,
        source_id: str | None = None,
        source_type: str | None = None,
    ) -> Entity:
        """Create a new entity."""
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"Invalid entity type: {entity_type}. Must be one of {ENTITY_TYPES}")

        entity = Entity(
            project_id=project_id,
            entity_type=entity_type,
            name=name,
            description=description,
            confidence=confidence,
            geometry_json=geometry_json,
            bbox_min_x=bbox[0] if bbox and len(bbox) > 0 else None,
            bbox_min_y=bbox[1] if bbox and len(bbox) > 1 else None,
            bbox_max_x=bbox[2] if bbox and len(bbox) > 2 else None,
            bbox_max_y=bbox[3] if bbox and len(bbox) > 3 else None,
            centroid_x=centroid[0] if centroid and len(centroid) > 0 else None,
            centroid_y=centroid[1] if centroid and len(centroid) > 1 else None,
            attributes_json=json.dumps(attributes) if attributes else None,
            tags_json=json.dumps(tags) if tags else None,
            analyst_notes=analyst_notes,
            observation_count=0,
            first_observed_at=datetime.utcnow(),
            last_observed_at=datetime.utcnow(),
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)

        # Record creation in history
        HistoryService.record_change(
            db, entity.id, "created", change_summary=f"Entity '{name}' created",
            changed_by="system", source_id=source_id, source_type=source_type,
        )

        logger.info(f"Created entity: {entity.name} ({entity.entity_type})")
        return entity

    @staticmethod
    def get_entity(db: Session, entity_id: str) -> Entity | None:
        """Get entity by ID."""
        return db.query(Entity).filter(Entity.id == entity_id).first()

    @staticmethod
    def list_entities(
        db: Session,
        project_id: str,
        entity_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
        tags: list[str] | None = None,
        favorite_only: bool = False,
        archived_only: bool = False,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[Entity], int]:
        """List entities with filtering and pagination."""
        q = db.query(Entity).filter(Entity.project_id == project_id)

        if entity_type:
            q = q.filter(Entity.entity_type == entity_type)
        if status:
            q = q.filter(Entity.status == status)
        if search:
            search_term = f"%{search}%"
            q = q.filter(
                or_(
                    Entity.name.ilike(search_term),
                    Entity.description.ilike(search_term),
                    Entity.analyst_notes.ilike(search_term),
                )
            )
        if favorite_only:
            q = q.filter(Entity.favorite == True)
        if archived_only:
            q = q.filter(Entity.archived == True)
        else:
            q = q.filter(Entity.archived == False)

        total = q.count()

        q = q.order_by(Entity.name)
        q = q.offset(page * min(page_size, MAX_PAGE_SIZE))
        q = q.limit(min(page_size, MAX_PAGE_SIZE))

        return q.all(), total

    @staticmethod
    def update_entity(
        db: Session,
        entity_id: str,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        confidence: float | None = None,
        geometry_json: str | None = None,
        bbox: list[float] | None = None,
        centroid: list[float] | None = None,
        attributes: dict | None = None,
        tags: list[str] | None = None,
        analyst_notes: str | None = None,
        favorite: bool | None = None,
        archived: bool | None = None,
        changed_by: str | None = None,
    ) -> Entity | None:
        """Update an existing entity."""
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if entity is None:
            return None

        if name is not None and name != entity.name:
            HistoryService.record_change(
                db, entity_id, "updated", field_name="name",
                old_value=entity.name, new_value=name,
                changed_by=changed_by,
            )
            entity.name = name

        if description is not None:
            entity.description = description

        if status is not None and status in ENTITY_STATUSES:
            if status != entity.status:
                HistoryService.record_change(
                    db, entity_id, "status_changed", field_name="status",
                    old_value=entity.status, new_value=status,
                    changed_by=changed_by,
                )
            entity.status = status

        if confidence is not None:
            entity.confidence = confidence

        if geometry_json is not None:
            entity.geometry_json = geometry_json

        if bbox is not None:
            entity.bbox_min_x = bbox[0] if len(bbox) > 0 else None
            entity.bbox_min_y = bbox[1] if len(bbox) > 1 else None
            entity.bbox_max_x = bbox[2] if len(bbox) > 2 else None
            entity.bbox_max_y = bbox[3] if len(bbox) > 3 else None

        if centroid is not None:
            entity.centroid_x = centroid[0] if len(centroid) > 0 else None
            entity.centroid_y = centroid[1] if len(centroid) > 1 else None

        if attributes is not None:
            HistoryService.record_change(
                db, entity_id, "attribute_changed", field_name="attributes",
                old_value=entity.attributes_json,
                new_value=json.dumps(attributes),
                changed_by=changed_by,
            )
            entity.attributes_json = json.dumps(attributes)

        if tags is not None:
            entity.tags_json = json.dumps(tags)

        if analyst_notes is not None:
            entity.analyst_notes = analyst_notes

        if favorite is not None:
            entity.favorite = favorite

        if archived is not None:
            entity.archived = archived

        db.commit()
        db.refresh(entity)
        logger.info(f"Updated entity: {entity.name}")
        return entity

    @staticmethod
    def delete_entity(db: Session, entity_id: str) -> bool:
        """Delete an entity and all related data."""
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if entity is None:
            return False

        # Delete related records
        db.query(EntityHistory).filter(EntityHistory.entity_id == entity_id).delete()
        db.query(EntityEvent).filter(EntityEvent.entity_id == entity_id).delete()
        db.query(EntityObservation).filter(
            EntityObservation.entity_id == entity_id
        ).delete()
        db.query(EntityRelationship).filter(
            or_(
                EntityRelationship.source_entity_id == entity_id,
                EntityRelationship.target_entity_id == entity_id,
            )
        ).delete(synchronize_session=False)

        db.delete(entity)
        db.commit()
        logger.info(f"Deleted entity: {entity.name} ({entity_id})")
        return True

    @staticmethod
    def add_observation(
        db: Session,
        entity_id: str,
        observation_type: str,
        source_id: str | None = None,
        source_type: str | None = None,
        confidence: float = DEFAULT_CONFIDENCE,
        geometry_json: str | None = None,
        attributes: dict | None = None,
        observed_at: datetime | None = None,
        analyst_notes: str | None = None,
    ) -> EntityObservation | None:
        """Add an observation to an entity."""
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if entity is None:
            return None

        obs = EntityObservation(
            entity_id=entity_id,
            observation_type=observation_type,
            source_id=source_id,
            source_type=source_type,
            confidence=confidence,
            geometry_json=geometry_json,
            attributes_json=json.dumps(attributes) if attributes else None,
            observed_at=observed_at or datetime.utcnow(),
            analyst_notes=analyst_notes,
        )
        db.add(obs)

        # Update entity observation counts and timestamps
        entity.observation_count += 1
        obs_time = obs.observed_at or datetime.utcnow()
        if entity.first_observed_at is None or obs_time < entity.first_observed_at:
            entity.first_observed_at = obs_time
        if entity.last_observed_at is None or obs_time > entity.last_observed_at:
            entity.last_observed_at = obs_time

        HistoryService.record_change(
            db, entity_id, "observation_added",
            change_summary=f"Observation '{observation_type}' added",
            source_id=source_id, source_type=source_type,
        )

        db.commit()
        db.refresh(obs)
        logger.info(f"Added observation to entity {entity.name}: {observation_type}")
        return obs

    @staticmethod
    def get_entity_observations(
        db: Session,
        entity_id: str,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[EntityObservation], int]:
        """List observations for an entity."""
        q = db.query(EntityObservation).filter(
            EntityObservation.entity_id == entity_id
        )
        total = q.count()
        observations = (
            q.order_by(EntityObservation.observed_at.desc())
            .offset(page * min(page_size, MAX_PAGE_SIZE))
            .limit(min(page_size, MAX_PAGE_SIZE))
            .all()
        )
        return observations, total

    @staticmethod
    def search_entities(
        db: Session,
        project_id: str,
        query: str,
        entity_types: list[str] | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Entity]:
        """Full-text search across entity fields."""
        q = db.query(Entity).filter(Entity.project_id == project_id)

        search_term = f"%{query}%"
        q = q.filter(
            or_(
                Entity.name.ilike(search_term),
                Entity.description.ilike(search_term),
                Entity.analyst_notes.ilike(search_term),
                Entity.entity_type.ilike(search_term),
                Entity.tags_json.ilike(search_term),
            )
        )

        if entity_types:
            q = q.filter(Entity.entity_type.in_(entity_types))
        if status:
            q = q.filter(Entity.status == status)

        return q.limit(limit).all()

    @staticmethod
    def get_entity_stats(db: Session, project_id: str) -> dict:
        """Get entity statistics for a project."""
        entities = db.query(Entity).filter(
            Entity.project_id == project_id,
            Entity.archived == False,
        ).all()

        type_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        total_observations = 0
        for e in entities:
            type_counts[e.entity_type] = type_counts.get(e.entity_type, 0) + 1
            status_counts[e.status] = status_counts.get(e.status, 0) + 1
            total_observations += e.observation_count

        total_relationships = db.query(EntityRelationship).join(
            Entity, EntityRelationship.source_entity_id == Entity.id
        ).filter(Entity.project_id == project_id).count()

        return {
            "total_entities": len(entities),
            "by_type": type_counts,
            "by_status": status_counts,
            "total_observations": total_observations,
            "total_relationships": total_relationships,
        }
