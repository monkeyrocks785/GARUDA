"""Timeline navigation service."""

from typing import Any

from sqlalchemy.orm import Session

from comparison_engine.config import (
    MAX_PLAYBACK_SPEED,
    MIN_PLAYBACK_SPEED,
    PLAYBACK_SPEEDS,
)
from comparison_engine.database.models import ComparisonSession


class TimelineService:
    """Manage timeline navigation for comparison sessions."""

    @staticmethod
    def set_position(
        db: Session,
        session_id: str,
        position: int,
    ) -> ComparisonSession | None:
        """Set the timeline position (frame/date index).

        Args:
            db: Database session.
            session_id: Comparison session ID.
            position: Timeline position index.

        Returns:
            Updated session or None.
        """
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        session.timeline_position = max(0, position)
        session.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def previous_date(
        db: Session,
        session_id: str,
    ) -> ComparisonSession | None:
        """Go to the previous date in the timeline.

        Returns:
            Updated session or None.
        """
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        session.timeline_position = max(0, (session.timeline_position or 0) - 1)
        session.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def next_date(
        db: Session,
        session_id: str,
        max_position: int = 1000,
    ) -> ComparisonSession | None:
        """Go to the next date in the timeline.

        Args:
            db: Database session.
            session_id: Comparison session ID.
            max_position: Maximum valid position.

        Returns:
            Updated session or None.
        """
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        session.timeline_position = min(
            max_position, (session.timeline_position or 0) + 1
        )
        session.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def jump_to_date(
        db: Session,
        session_id: str,
        position: int,
    ) -> ComparisonSession | None:
        """Jump to a specific date in the timeline.

        Alias for set_position with validation.
        """
        return TimelineService.set_position(db, session_id, position)

    @staticmethod
    def start_playback(
        db: Session,
        session_id: str,
        speed: float | None = None,
    ) -> ComparisonSession | None:
        """Start playback.

        Args:
            db: Database session.
            session_id: Comparison session ID.
            speed: Playback speed (default: 1.0).

        Returns:
            Updated session or None.
        """
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        session.is_playing = True
        if speed is not None:
            session.playback_speed = max(
                MIN_PLAYBACK_SPEED, min(MAX_PLAYBACK_SPEED, speed)
            )
        session.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def pause_playback(
        db: Session,
        session_id: str,
    ) -> ComparisonSession | None:
        """Pause playback."""
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        session.is_playing = False
        session.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def toggle_loop(
        db: Session,
        session_id: str,
    ) -> ComparisonSession | None:
        """Toggle loop mode."""
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        session.is_looping = not session.is_looping
        session.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def set_playback_speed(
        db: Session,
        session_id: str,
        speed: float,
    ) -> ComparisonSession | None:
        """Set playback speed."""
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        session.playback_speed = max(
            MIN_PLAYBACK_SPEED, min(MAX_PLAYBACK_SPEED, speed)
        )
        session.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_timeline_state(
        db: Session,
        session_id: str,
    ) -> dict[str, Any] | None:
        """Get current timeline state."""
        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            return None

        return {
            "position": session.timeline_position or 0,
            "is_playing": session.is_playing,
            "is_looping": session.is_looping,
            "playback_speed": session.playback_speed or 1.0,
            "available_speeds": PLAYBACK_SPEEDS,
        }
