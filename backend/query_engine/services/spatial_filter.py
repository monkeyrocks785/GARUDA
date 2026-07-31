"""Spatial Filter Service.

Applies spatial filter operations to entity queries.
Supports both SQLAlchemy-based filtering and in-memory post-filtering.
"""

import json
import logging

from sqlalchemy.orm import Session

from knowledge_engine.database.models import Entity

logger = logging.getLogger("garuda.query.spatial")


class SpatialFilterService:
    """Applies spatial constraints to entity queries."""

    @staticmethod
    def filter_bbox(
        query,
        bbox: list[float],
    ):
        """Filter entities within a bounding box.
        
        bbox: [min_x, min_y, max_x, max_y]
        """
        if len(bbox) != 4:
            return query
        min_x, min_y, max_x, max_y = bbox
        return query.filter(
            Entity.bbox_min_x >= min_x,
            Entity.bbox_min_y >= min_y,
            Entity.bbox_max_x <= max_x,
            Entity.bbox_max_y <= max_y,
        )

    @staticmethod
    def filter_within_aoi(
        db: Session,
        query,
        aoi_id: str,
    ):
        """Filter entities within an area of interest."""
        from models.aoi import AOI
        aoi = db.query(AOI).filter(AOI.id == aoi_id).first()
        if aoi is None:
            return query
        if aoi.bbox_min_x is not None and aoi.bbox_max_x is not None:
            return SpatialFilterService.filter_bbox(
                query,
                [aoi.bbox_min_x, aoi.bbox_min_y,
                 aoi.bbox_max_x, aoi.bbox_max_y],
            )
        return query

    @staticmethod
    def filter_intersects(
        query,
        geometry: dict,
    ):
        """Filter entities that intersect a geometry.
        
        Uses bounding-box overlap as a proxy for intersection.
        """
        coords = geometry.get("coordinates", [])
        if geometry.get("type") == "Point":
            x, y = coords
            return query.filter(
                Entity.centroid_x == x,
                Entity.centroid_y == y,
            )
        return query

    @staticmethod
    def filter_touches(
        query,
        geometry: dict,
    ):
        """Filter entities that touch a geometry.
        
        Currently uses bounding-box approximation.
        """
        coords = geometry.get("coordinates", [])
        if geometry.get("type") == "Point":
            x, y = coords
            return query.filter(
                Entity.centroid_x == x,
                Entity.centroid_y == y,
            )
        return query

    @staticmethod
    def apply_spatial_filter(
        db: Session,
        query,
        spatial: dict,
    ):
        """Apply a spatial filter clause to a SQLAlchemy query.
        
        Args:
            db: Database session.
            query: SQLAlchemy query on Entity model.
            spatial: Spatial filter dict from query builder.
            
        Returns:
            Filtered SQLAlchemy query.
        """
        operator = spatial.get("operator", "bbox")

        if operator == "bbox" and "bbox" in spatial:
            return SpatialFilterService.filter_bbox(query, spatial["bbox"])

        if operator == "within_aoi" and "aoi_id" in spatial:
            return SpatialFilterService.filter_within_aoi(db, query, spatial["aoi_id"])

        if operator == "intersects" and "geometry" in spatial:
            return SpatialFilterService.filter_intersects(query, spatial["geometry"])

        if operator == "touches" and "geometry" in spatial:
            return SpatialFilterService.filter_touches(query, spatial["geometry"])

        return query
