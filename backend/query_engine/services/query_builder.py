"""Query Builder Service.

Constructs structured filter objects that can be compiled into
SQLAlchemy queries by the QueryExecutor.
"""

import hashlib
import json

from query_engine.config import (
    CLASSIFICATION_LEVELS,
    ENTITY_TYPES,
    EVENT_TYPES,
    RELATIONSHIP_TYPES,
    REVIEW_STATUSES,
    SORT_DIRECTIONS,
    SPATIAL_OPERATORS,
    TEMPORAL_OPERATORS,
)


class QueryBuilder:
    """Builds and validates structured query filter objects.

    A query is a dict of filter clauses organized by category:

    {
        "entity_types": [...],
        "entity_name": "...",
        "mission": "...",
        "project_id": "...",
        "aoi": "...",
        "spatial": {...},
        "temporal": {...},
        "event_type": "...",
        "relationship": {...},
        "confidence": {"min": ..., "max": ...},
        "review_status": "...",
        "tags": [...],
        "classification": "...",
        "analyst": "...",
        "sort_by": "...",
        "sort_direction": "...",
        "max_results": ...,
        "page": 0,
        "page_size": 50,
    }
    """

    @staticmethod
    def build_base_query(
        project_id: str,
        entity_types: list[str] | None = None,
        entity_name: str | None = None,
        mission: str | None = None,
        aoi: str | None = None,
        event_type: str | None = None,
        relationship_type: str | None = None,
        confidence_min: float | None = None,
        confidence_max: float | None = None,
        review_status: str | None = None,
        tags: list[str] | None = None,
        classification: str | None = None,
        analyst: str | None = None,
        **kwargs,
    ) -> dict:
        """Build a query dict with validated filters."""
        query: dict = {"project_id": project_id}

        if entity_types:
            valid = [t for t in entity_types if t in ENTITY_TYPES]
            if valid:
                query["entity_types"] = valid

        if entity_name:
            query["entity_name"] = entity_name

        if mission:
            query["mission"] = mission

        if aoi:
            query["aoi"] = aoi

        if event_type:
            if event_type in EVENT_TYPES:
                query["event_type"] = event_type

        if relationship_type:
            if relationship_type in RELATIONSHIP_TYPES:
                query["relationship"] = {"relationship_type": relationship_type}

        if confidence_min is not None or confidence_max is not None:
            c: dict = {}
            if confidence_min is not None:
                c["min"] = max(0.0, min(1.0, confidence_min))
            if confidence_max is not None:
                c["max"] = max(0.0, min(1.0, confidence_max))
            query["confidence"] = c

        if review_status:
            if review_status in REVIEW_STATUSES:
                query["review_status"] = review_status

        if tags:
            query["tags"] = tags

        if classification:
            if classification in CLASSIFICATION_LEVELS:
                query["classification"] = classification

        if analyst:
            query["analyst"] = analyst

        # Default pagination
        query["page"] = kwargs.pop("page", 0)
        query["page_size"] = kwargs.pop("page_size", 50)
        query["max_results"] = kwargs.pop("max_results", 500)
        sort_by = kwargs.pop("sort_by", None)
        query["sort_by"] = sort_by if sort_by else "name"
        sort_dir = kwargs.pop("sort_direction", None)
        query["sort_direction"] = sort_dir if sort_dir and sort_dir in SORT_DIRECTIONS else "asc"

        return query

    @staticmethod
    def add_spatial_filter(
        query: dict,
        operator: str,
        geometry: dict | None = None,
        aoi_id: str | None = None,
        buffer_meters: float | None = None,
        distance_meters: float | None = None,
        nearest_count: int | None = None,
        bbox: list[float] | None = None,
    ) -> dict:
        """Add a spatial filter clause to an existing query."""
        if operator not in SPATIAL_OPERATORS:
            raise ValueError(
                f"Unsupported spatial operator: {operator}. "
                f"Supported: {SPATIAL_OPERATORS}"
            )

        spatial: dict = {"operator": operator}

        if geometry:
            spatial["geometry"] = geometry
        if aoi_id:
            spatial["aoi_id"] = aoi_id
        if buffer_meters is not None:
            spatial["buffer_meters"] = buffer_meters
        if distance_meters is not None:
            spatial["distance_meters"] = distance_meters
        if nearest_count is not None:
            spatial["nearest_count"] = nearest_count
        if bbox is not None and len(bbox) == 4:
            spatial["bbox"] = bbox

        query["spatial"] = spatial
        return query

    @staticmethod
    def add_temporal_filter(
        query: dict,
        operator: str,
        date: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        min_observations: int | None = None,
        max_observations: int | None = None,
        min_duration_days: int | None = None,
        max_duration_days: int | None = None,
    ) -> dict:
        """Add a temporal filter clause to an existing query."""
        if operator not in TEMPORAL_OPERATORS:
            raise ValueError(
                f"Unsupported temporal operator: {operator}. "
                f"Supported: {TEMPORAL_OPERATORS}"
            )

        temporal: dict = {"operator": operator}

        if date:
            temporal["date"] = date
        if date_from:
            temporal["date_from"] = date_from
        if date_to:
            temporal["date_to"] = date_to
        if min_observations is not None:
            temporal["min_observations"] = min_observations
        if max_observations is not None:
            temporal["max_observations"] = max_observations
        if min_duration_days is not None:
            temporal["min_duration_days"] = min_duration_days
        if max_duration_days is not None:
            temporal["max_duration_days"] = max_duration_days

        query["temporal"] = temporal
        return query

    @staticmethod
    def add_relationship_filter(
        query: dict,
        relationship_type: str,
        target_entity_id: str | None = None,
        target_entity_type: str | None = None,
        bidirectional: bool = False,
    ) -> dict:
        """Add a relationship filter to an existing query."""
        if relationship_type not in RELATIONSHIP_TYPES:
            raise ValueError(
                f"Unsupported relationship type: {relationship_type}. "
                f"Supported: {RELATIONSHIP_TYPES}"
            )

        rel: dict = {"relationship_type": relationship_type}

        if target_entity_id:
            rel["target_entity_id"] = target_entity_id
        if target_entity_type:
            rel["target_entity_type"] = target_entity_type
        rel["bidirectional"] = bidirectional

        query["relationship"] = rel
        return query

    @staticmethod
    def compute_query_hash(query: dict) -> str:
        """Compute a stable hash of a query dict for caching."""
        normalized = json.dumps(query, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()

    @staticmethod
    def serialize_query(query: dict) -> str:
        """Serialize a query dict to JSON string."""
        return json.dumps(query, default=str)

    @staticmethod
    def deserialize_query(query_json: str) -> dict:
        """Deserialize a JSON string back to a query dict."""
        return json.loads(query_json)
