"""Bookmark service for comparison sessions."""

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from comparison_engine.database.models import (
    ComparisonBookmark,
    ComparisonSession,
)


class BookmarkService:
    """Manage bookmarks for comparison sessions."""

    @staticmethod
    def create_bookmark(
        db: Session,
        session_id: str,
        name: str,
        description: str | None = None,
        timeline_position: int | None = None,
        map_state: dict[str, Any] | None = None,
        opacity: float | None = None,
        swipe_position: float | None = None,
        mode: str | None = None,
        view_settings: dict[str, Any] | None = None,
    ) -> ComparisonBookmark:
        """Create a new bookmark.

        Args:
            db: Database session.
            session_id: Comparison session ID.
            name: Bookmark name.
            description: Optional description.
            timeline_position: Saved timeline position.
            map_state: Saved map state dict.
            opacity: Saved opacity value.
            swipe_position: Saved swipe position.
            mode: Saved comparison mode.
            view_settings: Saved view settings dict.

        Returns:
            Created ComparisonBookmark.
        """
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        # Get next sort order
        last = (
            db.query(ComparisonBookmark)
            .filter(ComparisonBookmark.session_id == session_id)
            .order_by(ComparisonBookmark.sort_order.desc())
            .first()
        )
        next_order = (last.sort_order + 1) if last else 0

        bookmark = ComparisonBookmark(
            id=str(uuid.uuid4()),
            session_id=session_id,
            name=name,
            description=description,
            timeline_position=timeline_position,
            map_state=json.dumps(map_state) if map_state else None,
            opacity=opacity,
            swipe_position=swipe_position,
            mode=mode,
            view_settings=json.dumps(view_settings) if view_settings else None,
            sort_order=next_order,
        )
        db.add(bookmark)
        db.commit()
        db.refresh(bookmark)
        return bookmark

    @staticmethod
    def get_bookmarks(
        db: Session,
        session_id: str,
    ) -> list[ComparisonBookmark]:
        """Get all bookmarks for a session."""
        return (
            db.query(ComparisonBookmark)
            .filter(ComparisonBookmark.session_id == session_id)
            .order_by(ComparisonBookmark.sort_order)
            .all()
        )

    @staticmethod
    def update_bookmark(
        db: Session,
        bookmark_id: str,
        session_id: str,
        **kwargs,
    ) -> ComparisonBookmark | None:
        """Update a bookmark."""
        bookmark = (
            db.query(ComparisonBookmark)
            .filter(
                ComparisonBookmark.id == bookmark_id,
                ComparisonBookmark.session_id == session_id,
            )
            .first()
        )
        if bookmark is None:
            return None

        allowed = {
            "name", "description", "timeline_position", "map_state",
            "opacity", "swipe_position", "mode", "view_settings", "sort_order",
        }
        for key, value in kwargs.items():
            if key in allowed:
                if key in ("map_state", "view_settings") and isinstance(value, dict):
                    setattr(bookmark, key, json.dumps(value))
                else:
                    setattr(bookmark, key, value)

        db.commit()
        db.refresh(bookmark)
        return bookmark

    @staticmethod
    def delete_bookmark(
        db: Session,
        bookmark_id: str,
        session_id: str,
    ) -> bool:
        """Delete a bookmark."""
        bookmark = (
            db.query(ComparisonBookmark)
            .filter(
                ComparisonBookmark.id == bookmark_id,
                ComparisonBookmark.session_id == session_id,
            )
            .first()
        )
        if bookmark is None:
            return False
        db.delete(bookmark)
        db.commit()
        return True

    @staticmethod
    def to_dict(bookmark: ComparisonBookmark) -> dict[str, Any]:
        """Convert bookmark to dictionary."""
        return {
            "id": bookmark.id,
            "session_id": bookmark.session_id,
            "name": bookmark.name,
            "description": bookmark.description,
            "timeline_position": bookmark.timeline_position,
            "map_state": json.loads(bookmark.map_state) if bookmark.map_state else None,
            "opacity": bookmark.opacity,
            "swipe_position": bookmark.swipe_position,
            "mode": bookmark.mode,
            "view_settings": json.loads(bookmark.view_settings) if bookmark.view_settings else None,
            "sort_order": bookmark.sort_order,
            "created_at": bookmark.created_at.isoformat() if bookmark.created_at else None,
        }
