"""Temporal Engine - Database Models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class Timeline(Base):
    __tablename__ = "timelines"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_by: Mapped[str] = mapped_column(String(50), default="date", index=True)
    sort_order: Mapped[str] = mapped_column(String(20), default="asc")
    entry_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Timeline(id={self.id}, name={self.name}, entries={self.entry_count})>"


class TimelineEntry(Base):
    __tablename__ = "timeline_entries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    timeline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("timelines.id", ondelete="CASCADE"), index=True
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    acquisition_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    acquisition_time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sensor_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mission_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    aoi_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dataset_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    visibility: Mapped[bool] = mapped_column(Boolean, default=True)
    opacity: Mapped[float] = mapped_column(Float, default=1.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<TimelineEntry(id={self.id}, dataset_id={self.dataset_id}, date={self.acquisition_date})>"


class ComparisonSession(Base):
    __tablename__ = "comparison_sessions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    timeline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("timelines.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mode: Mapped[str] = mapped_column(String(50), default="side_by_side")
    left_entry_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    right_entry_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    swipe_position: Mapped[float] = mapped_column(Float, default=50.0)
    opacity: Mapped[float] = mapped_column(Float, default=1.0)
    linked_pan_zoom: Mapped[bool] = mapped_column(Boolean, default=True)
    map_center_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_center_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_zoom: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<ComparisonSession(id={self.id}, mode={self.mode})>"


class TimelineBookmark(Base):
    __tablename__ = "timeline_bookmarks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    timeline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("timelines.id", ondelete="CASCADE"), index=True
    )
    entry_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    bookmark_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<TimelineBookmark(id={self.id}, label={self.label})>"


class TimelineLog(Base):
    __tablename__ = "timeline_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    timeline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("timelines.id", ondelete="CASCADE"), index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<TimelineLog(id={self.id}, action={self.action})>"
