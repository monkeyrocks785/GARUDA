"""Query Executor Service.

Compiles structured query dicts into SQLAlchemy queries against the
knowledge engine's Entity model, applies filters, and returns results.
"""

import json
import logging
import time

from sqlalchemy import or_
from sqlalchemy.orm import Session

from knowledge_engine.database.models import Entity, EntityObservation
from query_engine.services.spatial_filter import SpatialFilterService
from query_engine.services.temporal_filter import TemporalFilterService

logger = logging.getLogger("garuda.query.executor")


class QueryExecutor:
    """Executes structured queries against the knowledge base."""

    @staticmethod
    def execute_query(
        db: Session,
        query: dict,
    ) -> dict:
        """Execute a structured query and return results.
        
        Args:
            db: Database session.
            query: Structured query dict from QueryBuilder.
            
        Returns:
            dict with keys: items, total, page, page_size, execution_time_ms
        """
        start = time.monotonic()
        project_id = query.get("project_id")
        if not project_id:
            return {
                "items": [],
                "total": 0,
                "page": 0,
                "page_size": 50,
                "execution_time_ms": 0,
            }

        q = db.query(Entity).filter(Entity.project_id == project_id)

        # ── Entity Types ────────────────────────────────────────────────
        entity_types = query.get("entity_types")
        if entity_types:
            q = q.filter(Entity.entity_type.in_(entity_types))

        # ── Entity Name ─────────────────────────────────────────────────
        entity_name = query.get("entity_name")
        if entity_name:
            q = q.filter(Entity.name.ilike(f"%{entity_name}%"))

        # ── Tags ────────────────────────────────────────────────────────
        tags = query.get("tags")
        if tags:
            tag_filters = [Entity.tags_json.ilike(f'%{t}%') for t in tags]
            q = q.filter(or_(*tag_filters))

        # ── Confidence ──────────────────────────────────────────────────
        confidence = query.get("confidence")
        if confidence:
            if "min" in confidence:
                q = q.filter(Entity.confidence >= confidence["min"])
            if "max" in confidence:
                q = q.filter(Entity.confidence <= confidence["max"])

        # ── Review Status ───────────────────────────────────────────────
        review_status = query.get("review_status")
        if review_status:
            q = q.filter(Entity.status == review_status)

        # ── Event Type ──────────────────────────────────────────────────
        event_type = query.get("event_type")
        if event_type:
            from knowledge_engine.database.models import EntityEvent
            q = q.filter(
                Entity.id.in_(
                    db.query(EntityEvent.entity_id).filter(
                        EntityEvent.event_type == event_type
                    ).subquery()
                )
            )

        # ── Relationship Filter ─────────────────────────────────────────
        relationship = query.get("relationship")
        if relationship:
            from knowledge_engine.database.models import EntityRelationship
            rel_type = relationship.get("relationship_type")
            target_id = relationship.get("target_entity_id")
            if rel_type:
                sub = db.query(EntityRelationship.source_entity_id).filter(
                    EntityRelationship.relationship_type == rel_type
                )
                if target_id:
                    sub = sub.filter(
                        EntityRelationship.target_entity_id == target_id
                    )
                q = q.filter(Entity.id.in_(sub.subquery()))

        # ── Spatial Filter ──────────────────────────────────────────────
        spatial = query.get("spatial")
        if spatial:
            q = SpatialFilterService.apply_spatial_filter(db, q, spatial)

        # ── Temporal Filter ─────────────────────────────────────────────
        temporal = query.get("temporal")
        if temporal:
            q = TemporalFilterService.apply_temporal_filter(q, temporal)

        # ── Archived ────────────────────────────────────────────────────
        q = q.filter(Entity.archived == False)

        # ── Sorting ─────────────────────────────────────────────────────
        sort_by = query.get("sort_by", "name")
        sort_dir = query.get("sort_direction", "asc")
        sort_col = getattr(Entity, sort_by, Entity.name)
        if sort_dir == "desc":
            sort_col = sort_col.desc()
        q = q.order_by(sort_col)

        # ── Pagination ──────────────────────────────────────────────────
        page = query.get("page", 0)
        page_size = query.get("page_size", 50)
        max_results = query.get("max_results", 500)
        page_size = min(page_size, max_results)

        total = q.count()
        items = q.offset(page * page_size).limit(page_size).all()

        elapsed = (time.monotonic() - start) * 1000

        return {
            "items": [entity.to_dict() for entity in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "execution_time_ms": round(elapsed, 2),
        }

    @staticmethod
    def execute_and_enrich(
        db: Session,
        query: dict,
    ) -> dict:
        """Execute query and enrich results with observations and event data."""
        result = QueryExecutor.execute_query(db, query)
        enriched = []
        for item in result["items"]:
            obs_count = (
                db.query(EntityObservation)
                .filter(EntityObservation.entity_id == item["id"])
                .count()
            )
            item["observation_count_actual"] = obs_count
            from knowledge_engine.database.models import EntityEvent, EntityRelationship
            event_count = (
                db.query(EntityEvent)
                .filter(EntityEvent.entity_id == item["id"])
                .count()
            )
            rel_count = (
                db.query(EntityRelationship)
                .filter(
                    or_(
                        EntityRelationship.source_entity_id == item["id"],
                        EntityRelationship.target_entity_id == item["id"],
                    )
                )
                .count()
            )
            item["event_count"] = event_count
            item["relationship_count"] = rel_count
            enriched.append(item)
        result["items"] = enriched
        return result
