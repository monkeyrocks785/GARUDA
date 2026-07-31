"""Database models for the Temporal Comparison Engine.

Adapted to the existing comparison_sessions table schema in the database.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class ComparisonSession(Base):
    """Stores comparison session metadata and state.

    Matches the existing comparison_sessions table in the database.
    """

    __tablename__ = "comparison_sessions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    timeline_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("timelines.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255))
    mode: Mapped[str] = mapped_column(String(50), default="side_by_side")
    left_entry_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("timeline_entries.id", ondelete="SET NULL"), nullable=True
    )
    right_entry_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("timeline_entries.id", ondelete="SET NULL"), nullable=True
    )
    swipe_position: Mapped[float] = mapped_column(Float, default=0.5)
    opacity: Mapped[float] = mapped_column(Float, default=1.0)
    linked_pan_zoom: Mapped[bool] = mapped_column(Boolean, default=True)
    map_center_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_center_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_zoom: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Extended fields (added by comparison engine)
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_paths: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_labels: Mapped[str | None] = mapped_column(Text, nullable=True)
    difference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    difference_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    sync_options: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeline_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    playback_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_playing: Mapped[bool] = mapped_column(Boolean, default=False)
    is_looping: Mapped[bool] = mapped_column(Boolean, default=False)
    layout_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    map_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    blink_interval_ms: Mapped[int] = mapped_column(Integer, default=1000)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    pipeline_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ComparisonView(Base):
    """Stores individual views within a comparison session."""

    __tablename__ = "comparison_views"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("comparison_sessions.id", ondelete="CASCADE"), index=True
    )
    view_index: Mapped[int] = mapped_column(Integer)
    dataset_path: Mapped[str] = mapped_column(Text)
    dataset_label: Mapped[str] = mapped_column(String(255))
    display_settings: Mapped[str | None] = mapped_column(Text, nullable=True)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ComparisonBookmark(Base):
    """Bookmarks for specific comparison states."""

    __tablename__ = "comparison_bookmarks"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("comparison_sessions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeline_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    map_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    opacity: Mapped[float | None] = mapped_column(Float, nullable=True)
    swipe_position: Mapped[float | None] = mapped_column(Float, nullable=True)
    mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    view_settings: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ComparisonAnnotation(Base):
    """Annotations and notes on comparison views."""

    __tablename__ = "comparison_annotations"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("comparison_sessions.id", ondelete="CASCADE"), index=True
    )
    annotation_type: Mapped[str] = mapped_column(String(50))
    geometry: Mapped[str] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(20), default="#FF0000")
    stroke_width: Mapped[int] = mapped_column(Integer, default=2)
    fill_opacity: Mapped[float] = mapped_column(Float, default=0.3)
    timeline_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    view_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ComparisonExport(Base):
    """Exported comparison results."""

    __tablename__ = "comparison_exports"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("comparison_sessions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    export_format: Mapped[str] = mapped_column(String(50))
    export_scope: Mapped[str] = mapped_column(String(50))
    output_path: Mapped[str] = mapped_column(Text)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    export_options: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ComparisonMeasurement(Base):
    """Measurements taken on comparison views."""

    __tablename__ = "comparison_measurements"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("comparison_sessions.id", ondelete="CASCADE"), index=True
    )
    measurement_type: Mapped[str] = mapped_column(String(50))
    unit: Mapped[str] = mapped_column(String(20), default="pixels")
    value: Mapped[float] = mapped_column(Float)
    geometry: Mapped[str] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timeline_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
