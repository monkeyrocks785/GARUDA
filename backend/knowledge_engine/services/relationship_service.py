"""Relationship Service.

Manages connections between entities in the knowledge graph.
"""

import json
import logging
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from knowledge_engine.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, RELATIONSHIP_TYPES
from knowledge_engine.database.models import Entity, EntityHistory, EntityRelationship
from knowledge_engine.services.history_service import HistoryService

logger = logging.getLogger("garuda.knowledge.relationship_service")


class RelationshipService:
    """CRUD operations for entity relationships."""

    @staticmethod
    def create_relationship(
        db: Session,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        confidence: float = 1.0,
        attributes: dict | None = None,
        description: str | None = None,
        bidirectional: bool = False,
        analyst_notes: str | None = None,
        source_id: str | None = None,
        source_type: str | None = None,
    ) -> EntityRelationship:
        """Create a relationship between two entities."""
        if relationship_type not in RELATIONSHIP_TYPES:
            raise ValueError(
                f"Invalid relationship type: {relationship_type}. "
                f"Must be one of {RELATIONSHIP_TYPES}"
            )

        source = db.query(Entity).filter(Entity.id == source_entity_id).first()
        if source is None:
            raise ValueError(f"Source entity not found: {source_entity_id}")

        target = db.query(Entity).filter(Entity.id == target_entity_id).first()
        if target is None:
            raise ValueError(f"Target entity not found: {target_entity_id}")

        if source_entity_id == target_entity_id:
            raise ValueError("Cannot create relationship from entity to itself")

        # Check for duplicate relationship
        existing = db.query(EntityRelationship).filter(
            EntityRelationship.source_entity_id == source_entity_id,
            EntityRelationship.target_entity_id == target_entity_id,
            EntityRelationship.relationship_type == relationship_type,
        ).first()
        if existing:
            raise ValueError(
                f"Relationship already exists: {source.name} -- "
                f"{relationship_type} --> {target.name}"
            )

        rel = EntityRelationship(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relationship_type=relationship_type,
            confidence=confidence,
            attributes_json=json.dumps(attributes) if attributes else None,
            description=description,
            bidirectional=bidirectional,
            analyst_notes=analyst_notes,
            source_id=source_id,
            source_type=source_type,
        )
        db.add(rel)

        HistoryService.record_change(
            db, source_entity_id, "relationship_added",
            change_summary=f"Relationship '{relationship_type}' to '{target.name}'",
            source_id=source_id, source_type=source_type,
        )
        HistoryService.record_change(
            db, target_entity_id, "relationship_added",
            change_summary=f"Relationship '{relationship_type}' from '{source.name}'",
            source_id=source_id, source_type=source_type,
        )

        db.commit()
        db.refresh(rel)
        logger.info(
            f"Created relationship: {source.name} -- "
            f"{relationship_type} --> {target.name}"
        )
        return rel

    @staticmethod
    def get_relationship(db: Session, relationship_id: str) -> EntityRelationship | None:
        """Get a relationship by ID."""
        return db.query(EntityRelationship).filter(
            EntityRelationship.id == relationship_id
        ).first()

    @staticmethod
    def list_relationships(
        db: Session,
        project_id: str,
        entity_id: str | None = None,
        relationship_type: str | None = None,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[dict], int]:
        """List relationships for a project, optionally filtered by entity or type."""
        q = (
            db.query(EntityRelationship)
            .join(Entity, EntityRelationship.source_entity_id == Entity.id)
            .filter(Entity.project_id == project_id)
        )

        if entity_id:
            q = q.filter(
                or_(
                    EntityRelationship.source_entity_id == entity_id,
                    EntityRelationship.target_entity_id == entity_id,
                )
            )

        if relationship_type:
            q = q.filter(EntityRelationship.relationship_type == relationship_type)

        total = q.count()
        relationships = (
            q.order_by(EntityRelationship.created_at.desc())
            .offset(page * min(page_size, MAX_PAGE_SIZE))
            .limit(min(page_size, MAX_PAGE_SIZE))
            .all()
        )

        # Enrich with entity names
        results = []
        for rel in relationships:
            source = db.query(Entity).filter(Entity.id == rel.source_entity_id).first()
            target = db.query(Entity).filter(Entity.id == rel.target_entity_id).first()
            d = rel.to_dict()
            d["source_entity_name"] = source.name if source else None
            d["target_entity_name"] = target.name if target else None
            d["source_entity_type"] = source.entity_type if source else None
            d["target_entity_type"] = target.entity_type if target else None
            results.append(d)

        return results, total

    @staticmethod
    def update_relationship(
        db: Session,
        relationship_id: str,
        confidence: float | None = None,
        attributes: dict | None = None,
        description: str | None = None,
        bidirectional: bool | None = None,
        analyst_notes: str | None = None,
        changed_by: str | None = None,
    ) -> EntityRelationship | None:
        """Update a relationship."""
        rel = db.query(EntityRelationship).filter(
            EntityRelationship.id == relationship_id
        ).first()
        if rel is None:
            return None

        if confidence is not None:
            rel.confidence = confidence
        if attributes is not None:
            rel.attributes_json = json.dumps(attributes)
        if description is not None:
            rel.description = description
        if bidirectional is not None:
            rel.bidirectional = bidirectional
        if analyst_notes is not None:
            rel.analyst_notes = analyst_notes

        db.commit()
        db.refresh(rel)
        logger.info(f"Updated relationship: {rel.id}")
        return rel

    @staticmethod
    def delete_relationship(db: Session, relationship_id: str) -> bool:
        """Delete a relationship."""
        rel = db.query(EntityRelationship).filter(
            EntityRelationship.id == relationship_id
        ).first()
        if rel is None:
            return False

        source = db.query(Entity).filter(Entity.id == rel.source_entity_id).first()
        target = db.query(Entity).filter(Entity.id == rel.target_entity_id).first()

        HistoryService.record_change(
            db, rel.source_entity_id, "relationship_removed",
            change_summary=f"Relationship '{rel.relationship_type}' to "
            f"'{target.name if target else 'unknown'}' removed",
        )
        HistoryService.record_change(
            db, rel.target_entity_id, "relationship_removed",
            change_summary=f"Relationship '{rel.relationship_type}' from "
            f"'{source.name if source else 'unknown'}' removed",
        )

        db.delete(rel)
        db.commit()
        logger.info(f"Deleted relationship: {relationship_id}")
        return True

    @staticmethod
    def get_entity_neighbors(
        db: Session,
        entity_id: str,
        relationship_type: str | None = None,
        direction: str = "both",
    ) -> list[dict]:
        """Get all entities connected to a given entity."""
        results = []

        if direction in ("outgoing", "both"):
            outgoing = db.query(EntityRelationship).filter(
                EntityRelationship.source_entity_id == entity_id
            )
            if relationship_type:
                outgoing = outgoing.filter(
                    EntityRelationship.relationship_type == relationship_type
                )
            for rel in outgoing.all():
                target = db.query(Entity).filter(
                    Entity.id == rel.target_entity_id
                ).first()
                if target:
                    results.append({
                        "entity": target.to_dict(),
                        "relationship": rel.to_dict(),
                        "direction": "outgoing",
                    })

        if direction in ("incoming", "both"):
            incoming = db.query(EntityRelationship).filter(
                EntityRelationship.target_entity_id == entity_id
            )
            if relationship_type:
                incoming = incoming.filter(
                    EntityRelationship.relationship_type == relationship_type
                )
            for rel in incoming.all():
                source = db.query(Entity).filter(
                    Entity.id == rel.source_entity_id
                ).first()
                if source:
                    results.append({
                        "entity": source.to_dict(),
                        "relationship": rel.to_dict(),
                        "direction": "incoming",
                    })

        return results
