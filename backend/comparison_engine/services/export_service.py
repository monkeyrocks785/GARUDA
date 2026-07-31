"""Export service for comparison sessions."""

import json
import os
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from comparison_engine.config import EXPORT_FORMATS, EXPORT_SCOPES
from comparison_engine.database.models import (
    ComparisonExport,
    ComparisonSession,
)


class ExportService:
    """Export comparison sessions and views."""

    @staticmethod
    def create_export(
        db: Session,
        session_id: str,
        name: str,
        export_format: str,
        export_scope: str,
        export_options: dict[str, Any] | None = None,
    ) -> ComparisonExport:
        """Create an export record.

        Args:
            db: Database session.
            session_id: Comparison session ID.
            name: Export name.
            export_format: Export format (png, tiff, pdf, json).
            export_scope: Export scope (current_view, all_views, etc.).
            export_options: Additional export options.

        Returns:
            Created ComparisonExport.

        Raises:
            ValueError: If invalid format or scope.
        """
        if export_format not in EXPORT_FORMATS:
            raise ValueError(
                f"Unsupported format: {export_format}. "
                f"Supported: {', '.join(EXPORT_FORMATS.keys())}"
            )
        if export_scope not in EXPORT_SCOPES:
            raise ValueError(
                f"Unsupported scope: {export_scope}. "
                f"Supported: {', '.join(EXPORT_SCOPES.keys())}"
            )

        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        export_id = str(uuid.uuid4())
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "storage", "comparison_exports", session_id
        )
        os.makedirs(output_dir, exist_ok=True)

        output_filename = f"{export_id}.{export_format}"
        output_path = os.path.join(output_dir, output_filename)

        export = ComparisonExport(
            id=export_id,
            session_id=session_id,
            name=name,
            export_format=export_format,
            export_scope=export_scope,
            output_path=output_path,
            export_options=json.dumps(export_options) if export_options else None,
            status="completed",
            completed_at=datetime.utcnow(),
        )
        db.add(export)
        db.commit()
        db.refresh(export)
        return export

    @staticmethod
    def list_exports(
        db: Session,
        session_id: str,
    ) -> list[ComparisonExport]:
        """List all exports for a session."""
        return (
            db.query(ComparisonExport)
            .filter(ComparisonExport.session_id == session_id)
            .order_by(ComparisonExport.created_at.desc())
            .all()
        )

    @staticmethod
    def delete_export(
        db: Session,
        export_id: str,
    ) -> bool:
        """Delete an export record and file."""
        export = db.query(ComparisonExport).get(export_id)
        if export is None:
            return False

        if export.output_path and os.path.exists(export.output_path):
            try:
                os.remove(export.output_path)
            except OSError:
                pass

        db.delete(export)
        db.commit()
        return True

    @staticmethod
    def export_session_json(
        db: Session,
        session_id: str,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Export session state as JSON.

        Args:
            db: Database session.
            session_id: Comparison session ID.
            output_dir: Directory to save the JSON file.

        Returns:
            Dictionary with session state data.
        """
        from comparison_engine.services.session_service import SessionService

        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        views = SessionService.get_views(db, session_id)
        from comparison_engine.database.models import (
            ComparisonAnnotation,
            ComparisonBookmark,
            ComparisonMeasurement,
        )

        bookmarks = (
            db.query(ComparisonBookmark)
            .filter(ComparisonBookmark.session_id == session_id)
            .order_by(ComparisonBookmark.sort_order)
            .all()
        )
        annotations = (
            db.query(ComparisonAnnotation)
            .filter(ComparisonAnnotation.session_id == session_id)
            .all()
        )
        measurements = (
            db.query(ComparisonMeasurement)
            .filter(ComparisonMeasurement.session_id == session_id)
            .all()
        )

        data = {
            "session": SessionService.to_dict(session),
            "views": [SessionService.view_to_dict(v) for v in views],
            "bookmarks": [
                {
                    "id": b.id,
                    "name": b.name,
                    "description": b.description,
                    "timeline_position": b.timeline_position,
                    "map_state": json.loads(b.map_state) if b.map_state else None,
                    "mode": b.mode,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                }
                for b in bookmarks
            ],
            "annotations": [
                {
                    "id": a.id,
                    "annotation_type": a.annotation_type,
                    "geometry": json.loads(a.geometry) if a.geometry else None,
                    "label": a.label,
                    "notes": a.notes,
                    "color": a.color,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in annotations
            ],
            "measurements": [
                {
                    "id": m.id,
                    "measurement_type": m.measurement_type,
                    "unit": m.unit,
                    "value": m.value,
                    "geometry": json.loads(m.geometry) if m.geometry else None,
                    "label": m.label,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in measurements
            ],
        }

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"session_{session_id}.json")
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
            data["output_path"] = output_path

        return data

    @staticmethod
    def to_dict(export: ComparisonExport) -> dict[str, Any]:
        """Convert export to dictionary."""
        return {
            "id": export.id,
            "session_id": export.session_id,
            "name": export.name,
            "export_format": export.export_format,
            "export_scope": export.export_scope,
            "output_path": export.output_path,
            "file_size": export.file_size,
            "export_options": json.loads(export.export_options) if export.export_options else None,
            "status": export.status,
            "error_message": export.error_message,
            "created_at": export.created_at.isoformat() if export.created_at else None,
            "completed_at": export.completed_at.isoformat() if export.completed_at else None,
        }
