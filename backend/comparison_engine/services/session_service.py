"""Session management service for comparison sessions."""

import json
import os
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from comparison_engine.config import (
    DEFAULT_COMPARISON_MODE,
    DEFAULT_PLAYBACK_SPEED,
    DEFAULT_SYNC_OPTIONS,
    SUPPORTED_EXTENSIONS,
)
from comparison_engine.database.models import (
    ComparisonSession,
    ComparisonView,
)


class SessionService:
    """Manage comparison sessions — create, read, update, delete, state."""

    @staticmethod
    def create_session(
        db: Session,
        project_id: str,
        name: str,
        dataset_paths: list[str],
        dataset_labels: list[str] | None = None,
        description: str | None = None,
        mode: str = DEFAULT_COMPARISON_MODE,
    ) -> ComparisonSession:
        """Create a new comparison session.

        Args:
            db: Database session.
            project_id: Project ID.
            name: Session name.
            dataset_paths: List of raster file paths to compare.
            dataset_labels: Optional labels for each dataset.
            description: Optional description.
            mode: Comparison mode.

        Returns:
            Created ComparisonSession.

        Raises:
            ValueError: If fewer than 2 datasets or unsupported format.
        """
        if len(dataset_paths) < 2:
            raise ValueError("At least 2 datasets required for comparison")

        for path in dataset_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Dataset not found: {path}")
            ext = os.path.splitext(path)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                raise ValueError(f"Unsupported format: {ext}")

        if dataset_labels is None:
            dataset_labels = [
                os.path.splitext(os.path.basename(p))[0]
                for p in dataset_paths
            ]
        elif len(dataset_labels) != len(dataset_paths):
            raise ValueError("dataset_labels length must match dataset_paths")

        session_id = str(uuid.uuid4())
        session = ComparisonSession(
            id=session_id,
            project_id=project_id,
            name=name,
            description=description,
            dataset_paths=json.dumps(dataset_paths),
            dataset_labels=json.dumps(dataset_labels),
            mode=mode,
            sync_options=json.dumps(DEFAULT_SYNC_OPTIONS),
            timeline_position=0,
            playback_speed=DEFAULT_PLAYBACK_SPEED,
            status="active",
        )
        db.add(session)

        # Create views
        for i, (path, label) in enumerate(zip(dataset_paths, dataset_labels)):
            view = ComparisonView(
                id=str(uuid.uuid4()),
                session_id=session_id,
                view_index=i,
                dataset_path=path,
                dataset_label=label,
            )
            db.add(view)

        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(
        db: Session,
        session_id: str,
    ) -> ComparisonSession | None:
        """Get a comparison session by ID."""
        session = db.query(ComparisonSession).get(session_id)
        if session and session.status != "deleted":
            session.last_opened_at = datetime.utcnow()
            db.commit()
            return session
        return None

    @staticmethod
    def list_sessions(
        db: Session,
        project_id: str,
        status: str | None = None,
        favorite: bool | None = None,
        archived: bool = False,
    ) -> list[ComparisonSession]:
        """List comparison sessions for a project."""
        query = (
            db.query(ComparisonSession)
            .filter(
                ComparisonSession.project_id == project_id,
                ComparisonSession.archived == archived,
                ComparisonSession.status != "deleted",
            )
        )
        if status:
            query = query.filter(ComparisonSession.status == status)
        if favorite is not None:
            query = query.filter(ComparisonSession.favorite == favorite)
        return query.order_by(ComparisonSession.created_at.desc()).all()

    @staticmethod
    def update_session(
        db: Session,
        session_id: str,
        **kwargs,
    ) -> ComparisonSession | None:
        """Update a comparison session.

        Accepted kwargs: name, description, mode, difference_type,
        difference_threshold, opacity, swipe_position, blink_interval_ms,
        timeline_position, playback_speed, is_playing, is_looping,
        layout_state, map_state, sync_options.
        """
        session = db.query(ComparisonSession).get(session_id)
        if session is None or session.status == "deleted":
            return None

        allowed = {
            "name", "description", "mode", "difference_type",
            "difference_threshold", "opacity", "swipe_position",
            "blink_interval_ms", "timeline_position", "playback_speed",
            "is_playing", "is_looping", "layout_state", "map_state",
            "sync_options", "status", "favorite", "archived",
        }

        for key, value in kwargs.items():
            if key in allowed:
                setattr(session, key, value)

        session.modified_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def delete_session(
        db: Session,
        session_id: str,
    ) -> bool:
        """Soft-delete a comparison session."""
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return False
        session.status = "deleted"
        session.modified_at = datetime.utcnow()
        db.commit()
        return True

    @staticmethod
    def toggle_favorite(
        db: Session,
        session_id: str,
    ) -> ComparisonSession | None:
        """Toggle favorite status."""
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None
        session.favorite = not session.favorite
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_views(
        db: Session,
        session_id: str,
    ) -> list[ComparisonView]:
        """Get all views for a session."""
        return (
            db.query(ComparisonView)
            .filter(ComparisonView.session_id == session_id)
            .order_by(ComparisonView.view_index)
            .all()
        )

    @staticmethod
    def update_view(
        db: Session,
        view_id: str,
        session_id: str,
        **kwargs,
    ) -> ComparisonView | None:
        """Update a comparison view."""
        view = (
            db.query(ComparisonView)
            .filter(
                ComparisonView.id == view_id,
                ComparisonView.session_id == session_id,
            )
            .first()
        )
        if view is None:
            return None

        allowed = {"display_settings", "visible", "dataset_label"}
        for key, value in kwargs.items():
            if key in allowed:
                setattr(view, key, value)

        view.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(view)
        return view

    @staticmethod
    def to_dict(session: ComparisonSession) -> dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "id": session.id,
            "project_id": session.project_id,
            "name": session.name,
            "description": session.description,
            "dataset_paths": json.loads(session.dataset_paths) if session.dataset_paths else [],
            "dataset_labels": json.loads(session.dataset_labels) if session.dataset_labels else [],
            "mode": session.mode,
            "difference_type": session.difference_type,
            "difference_threshold": session.difference_threshold,
            "sync_options": json.loads(session.sync_options) if session.sync_options else [],
            "timeline_position": session.timeline_position,
            "playback_speed": session.playback_speed,
            "is_playing": session.is_playing,
            "is_looping": session.is_looping,
            "layout_state": json.loads(session.layout_state) if session.layout_state else None,
            "map_state": json.loads(session.map_state) if session.map_state else None,
            "opacity": session.opacity,
            "swipe_position": session.swipe_position,
            "blink_interval_ms": session.blink_interval_ms,
            "status": session.status,
            "error_message": session.error_message,
            "pipeline_id": session.pipeline_id,
            "favorite": session.favorite,
            "archived": session.archived,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "modified_at": session.modified_at.isoformat() if session.modified_at else None,
            "last_opened_at": session.last_opened_at.isoformat() if session.last_opened_at else None,
        }

    @staticmethod
    def view_to_dict(view: ComparisonView) -> dict[str, Any]:
        """Convert view to dictionary."""
        return {
            "id": view.id,
            "session_id": view.session_id,
            "view_index": view.view_index,
            "dataset_path": view.dataset_path,
            "dataset_label": view.dataset_label,
            "display_settings": json.loads(view.display_settings) if view.display_settings else None,
            "visible": view.visible,
            "created_at": view.created_at.isoformat() if view.created_at else None,
            "updated_at": view.updated_at.isoformat() if view.updated_at else None,
        }
