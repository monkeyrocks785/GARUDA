"""Annotation service for comparison views."""

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from comparison_engine.config import ANNOTATION_SHAPES
from comparison_engine.database.models import (
    ComparisonAnnotation,
    ComparisonSession,
)


class AnnotationService:
    """Manage annotations on comparison views."""

    @staticmethod
    def create_annotation(
        db: Session,
        session_id: str,
        annotation_type: str,
        geometry: dict[str, Any],
        label: str | None = None,
        notes: str | None = None,
        color: str = "#FF0000",
        stroke_width: int = 2,
        fill_opacity: float = 0.3,
        timeline_position: int | None = None,
        view_index: int | None = None,
    ) -> ComparisonAnnotation:
        """Create a new annotation.

        Args:
            db: Database session.
            session_id: Comparison session ID.
            annotation_type: Type of annotation (point, line, polygon, etc.).
            geometry: Geometry dict with coordinates.
            label: Optional label text.
            notes: Optional notes text.
            color: Color hex string.
            stroke_width: Stroke width in pixels.
            fill_opacity: Fill opacity (0.0-1.0).
            timeline_position: Timeline position when created.
            view_index: Associated view index.

        Returns:
            Created ComparisonAnnotation.

        Raises:
            ValueError: If invalid annotation type.
        """
        if annotation_type not in ANNOTATION_SHAPES:
            raise ValueError(
                f"Invalid annotation type: {annotation_type}. "
                f"Supported: {', '.join(ANNOTATION_SHAPES.keys())}"
            )

        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        annotation = ComparisonAnnotation(
            id=str(uuid.uuid4()),
            session_id=session_id,
            annotation_type=annotation_type,
            geometry=json.dumps(geometry),
            label=label,
            notes=notes,
            color=color,
            stroke_width=stroke_width,
            fill_opacity=fill_opacity,
            timeline_position=timeline_position,
            view_index=view_index,
        )
        db.add(annotation)
        db.commit()
        db.refresh(annotation)
        return annotation

    @staticmethod
    def get_annotations(
        db: Session,
        session_id: str,
        annotation_type: str | None = None,
        view_index: int | None = None,
    ) -> list[ComparisonAnnotation]:
        """Get annotations for a session, optionally filtered."""
        query = (
            db.query(ComparisonAnnotation)
            .filter(ComparisonAnnotation.session_id == session_id)
        )
        if annotation_type:
            query = query.filter(ComparisonAnnotation.annotation_type == annotation_type)
        if view_index is not None:
            query = query.filter(ComparisonAnnotation.view_index == view_index)
        return query.order_by(ComparisonAnnotation.created_at).all()

    @staticmethod
    def update_annotation(
        db: Session,
        annotation_id: str,
        session_id: str,
        **kwargs,
    ) -> ComparisonAnnotation | None:
        """Update an annotation."""
        annotation = (
            db.query(ComparisonAnnotation)
            .filter(
                ComparisonAnnotation.id == annotation_id,
                ComparisonAnnotation.session_id == session_id,
            )
            .first()
        )
        if annotation is None:
            return None

        allowed = {
            "label", "notes", "color", "stroke_width", "fill_opacity", "geometry",
        }
        for key, value in kwargs.items():
            if key in allowed:
                if key == "geometry":
                    setattr(annotation, key, json.dumps(value))
                else:
                    setattr(annotation, key, value)

        annotation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(annotation)
        return annotation

    @staticmethod
    def delete_annotation(
        db: Session,
        annotation_id: str,
        session_id: str,
    ) -> bool:
        """Delete an annotation."""
        annotation = (
            db.query(ComparisonAnnotation)
            .filter(
                ComparisonAnnotation.id == annotation_id,
                ComparisonAnnotation.session_id == session_id,
            )
            .first()
        )
        if annotation is None:
            return False
        db.delete(annotation)
        db.commit()
        return True

    @staticmethod
    def delete_all_annotations(
        db: Session,
        session_id: str,
    ) -> int:
        """Delete all annotations for a session."""
        annotations = (
            db.query(ComparisonAnnotation)
            .filter(ComparisonAnnotation.session_id == session_id)
            .all()
        )
        count = len(annotations)
        for a in annotations:
            db.delete(a)
        db.commit()
        return count

    @staticmethod
    def to_dict(annotation: ComparisonAnnotation) -> dict[str, Any]:
        """Convert annotation to dictionary."""
        return {
            "id": annotation.id,
            "session_id": annotation.session_id,
            "annotation_type": annotation.annotation_type,
            "geometry": json.loads(annotation.geometry) if annotation.geometry else None,
            "label": annotation.label,
            "notes": annotation.notes,
            "color": annotation.color,
            "stroke_width": annotation.stroke_width,
            "fill_opacity": annotation.fill_opacity,
            "timeline_position": annotation.timeline_position,
            "view_index": annotation.view_index,
            "created_at": annotation.created_at.isoformat() if annotation.created_at else None,
            "updated_at": annotation.updated_at.isoformat() if annotation.updated_at else None,
        }
