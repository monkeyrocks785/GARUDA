"""Search Service.

Provides advanced search capabilities across entities, relationships,
events, and history in the knowledge graph.
"""

import json
import logging
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from knowledge_engine.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from knowledge_engine.database.models import (
    Entity,
    EntityEvent,
    EntityHistory,
    EntityObservation,
    EntityRelationship,
)

logger = logging.getLogger("garuda.knowledge.search_service")


class SearchService:
    """Advanced search operations."""

    @staticmethod
    def search_entities(
        db: Session,
        project_id: str,
        query: str,
        entity_types: list[str] | None = None,
        statuses: list[str] | None = None,
        tags: list[str] | None = None,
        min_confidence: float | None = None,
        has_observations: bool | None = None,
        has_relationships: bool | None = None,
        geometry_bbox: list[float] | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Full-text and attribute search across entities."""
        q = db.query(Entity).filter(Entity.project_id == project_id)

        search_term = f"%{query}%"
        q = q.filter(
            or_(
                Entity.name.ilike(search_term),
                Entity.description.ilike(search_term),
                Entity.analyst_notes.ilike(search_term),
                Entity.entity_type.ilike(search_term),
                Entity.tags_json.ilike(search_term),
                Entity.attributes_json.ilike(search_term),
            )
        )

        if entity_types:
            q = q.filter(Entity.entity_type.in_(entity_types))
        if statuses:
            q = q.filter(Entity.status.in_(statuses))
        if min_confidence is not None:
            q = q.filter(Entity.confidence >= min_confidence)
        if tags:
            for tag in tags:
                q = q.filter(Entity.tags_json.ilike(f"%{tag}%"))
        if geometry_bbox and len(geometry_bbox) == 4:
            q = q.filter(
                Entity.bbox_min_x <= geometry_bbox[2],
                Entity.bbox_max_x >= geometry_bbox[0],
                Entity.bbox_min_y <= geometry_bbox[3],
                Entity.bbox_max_y >= geometry_bbox[1],
            )

        entities = q.limit(limit).all()
        results = []
        for e in entities:
            d = e.to_dict()

            if has_observations is not None:
                obs_count = db.query(EntityObservation).filter(
                    EntityObservation.entity_id == e.id
                ).count()
                if has_observations and obs_count == 0:
                    continue
                if not has_observations and obs_count > 0:
                    continue

            if has_relationships is not None:
                rel_count = db.query(EntityRelationship).filter(
                    or_(
                        EntityRelationship.source_entity_id == e.id,
                        EntityRelationship.target_entity_id == e.id,
                    )
                ).count()
                if has_relationships and rel_count == 0:
                    continue
                if not has_relationships and rel_count > 0:
                    continue

            results.append(d)

        return results

    @staticmethod
    def search_relationships(
        db: Session,
        project_id: str,
        relationship_type: str | None = None,
        entity_type: str | None = None,
        min_confidence: float | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Search relationships with filters."""
        q = (
            db.query(EntityRelationship)
            .join(Entity, EntityRelationship.source_entity_id == Entity.id)
            .filter(Entity.project_id == project_id)
        )

        if relationship_type:
            q = q.filter(EntityRelationship.relationship_type == relationship_type)
        if min_confidence is not None:
            q = q.filter(EntityRelationship.confidence >= min_confidence)

        rels = q.limit(limit).all()
        results = []
        for rel in rels:
            source = db.query(Entity).filter(Entity.id == rel.source_entity_id).first()
            target = db.query(Entity).filter(Entity.id == rel.target_entity_id).first()

            if entity_type:
                if (source and source.entity_type != entity_type) and \
                   (target and target.entity_type != entity_type):
                    continue

            d = rel.to_dict()
            d["source_entity_name"] = source.name if source else None
            d["target_entity_name"] = target.name if target else None
            d["source_entity_type"] = source.entity_type if source else None
            d["target_entity_type"] = target.entity_type if target else None
            results.append(d)

        return results

    @staticmethod
    def search_events(
        db: Session,
        project_id: str,
        event_type: str | None = None,
        entity_type: str | None = None,
        query: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Search events across a project."""
        q = (
            db.query(EntityEvent)
            .join(Entity, EntityEvent.entity_id == Entity.id)
            .filter(Entity.project_id == project_id)
        )

        if event_type:
            q = q.filter(EntityEvent.event_type == event_type)
        if entity_type:
            q = q.filter(Entity.entity_type == entity_type)
        if query:
            search_term = f"%{query}%"
            q = q.filter(
                or_(
                    EntityEvent.description.ilike(search_term),
                    EntityEvent.analyst_notes.ilike(search_term),
                )
            )

        events = q.order_by(EntityEvent.event_time.desc()).limit(limit).all()
        results = []
        for ev in events:
            entity = db.query(Entity).filter(Entity.id == ev.entity_id).first()
            d = ev.to_dict()
            d["entity_name"] = entity.name if entity else None
            d["entity_type"] = entity.entity_type if entity else None
            results.append(d)

        return results

    @staticmethod
    def get_statistics(db: Session, project_id: str) -> dict:
        """Get comprehensive statistics for a project's knowledge graph."""
        entities = db.query(Entity).filter(
            Entity.project_id == project_id
        ).all()

        entity_type_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        total_observations = 0
        total_confidence = 0.0
        entity_ids = set()

        for e in entities:
            entity_type_counts[e.entity_type] = entity_type_counts.get(e.entity_type, 0) + 1
            status_counts[e.status] = status_counts.get(e.status, 0) + 1
            total_observations += e.observation_count
            total_confidence += e.confidence
            entity_ids.add(e.id)

        avg_confidence = total_confidence / len(entities) if entities else 0.0

        relationships = (
            db.query(EntityRelationship)
            .join(Entity, EntityRelationship.source_entity_id == Entity.id)
            .filter(Entity.project_id == project_id)
            .all()
        )
        rel_type_counts: dict[str, int] = {}
        for r in relationships:
            rel_type_counts[r.relationship_type] = rel_type_counts.get(r.relationship_type, 0) + 1

        events = (
            db.query(EntityEvent)
            .join(Entity, EntityEvent.entity_id == Entity.id)
            .filter(Entity.project_id == project_id)
            .all()
        )
        event_type_counts: dict[str, int] = {}
        for ev in events:
            event_type_counts[ev.event_type] = event_type_counts.get(ev.event_type, 0) + 1

        return {
            "entities": {
                "total": len(entities),
                "by_type": entity_type_counts,
                "by_status": status_counts,
                "avg_confidence": round(avg_confidence, 3),
            },
            "relationships": {
                "total": len(relationships),
                "by_type": rel_type_counts,
            },
            "events": {
                "total": len(events),
                "by_type": event_type_counts,
            },
            "observations": {
                "total": total_observations,
            },
        }
