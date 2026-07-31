"""Synchronization service for comparison views."""

import json
from typing import Any

from sqlalchemy.orm import Session

from comparison_engine.config import SYNC_OPTIONS
from comparison_engine.database.models import ComparisonSession


class SyncService:
    """Manage synchronization between comparison views."""

    @staticmethod
    def get_sync_options(
        db: Session,
        session_id: str,
    ) -> dict[str, Any] | None:
        """Get current synchronization options for a session."""
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        enabled = json.loads(session.sync_options) if session.sync_options else []
        return {
            "session_id": session_id,
            "enabled": enabled,
            "available": list(SYNC_OPTIONS.keys()),
            "labels": SYNC_OPTIONS,
        }

    @staticmethod
    def set_sync_options(
        db: Session,
        session_id: str,
        enabled: list[str],
    ) -> ComparisonSession | None:
        """Set synchronization options for a session.

        Args:
            db: Database session.
            session_id: Comparison session ID.
            enabled: List of sync option keys to enable.

        Returns:
            Updated session or None.
        """
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        # Validate all options
        for opt in enabled:
            if opt not in SYNC_OPTIONS:
                raise ValueError(f"Unknown sync option: {opt}")

        session.sync_options = json.dumps(enabled)
        session.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def toggle_sync_option(
        db: Session,
        session_id: str,
        option: str,
    ) -> ComparisonSession | None:
        """Toggle a single sync option."""
        if option not in SYNC_OPTIONS:
            raise ValueError(f"Unknown sync option: {option}")

        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        enabled = json.loads(session.sync_options) if session.sync_options else []
        if option in enabled:
            enabled.remove(option)
        else:
            enabled.append(option)

        session.sync_options = json.dumps(enabled)
        session.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def update_map_state(
        db: Session,
        session_id: str,
        center: list[float] | None = None,
        zoom: float | None = None,
        rotation: float | None = None,
    ) -> ComparisonSession | None:
        """Update synchronized map state (center, zoom, rotation)."""
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        state = json.loads(session.map_state) if session.map_state else {}
        if center is not None:
            state["center"] = center
        if zoom is not None:
            state["zoom"] = zoom
        if rotation is not None:
            state["rotation"] = rotation

        session.map_state = json.dumps(state)
        session.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_map_state(
        db: Session,
        session_id: str,
    ) -> dict[str, Any] | None:
        """Get synchronized map state."""
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        return json.loads(session.map_state) if session.map_state else {
            "center": [0, 0],
            "zoom": 1,
            "rotation": 0,
        }
