"""Project model for GARUDA geospatial intelligence platform."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class Project(Base):
    """Project entity - the core unit of work in GARUDA.

    Every satellite download, AI result, report, map layer, prediction,
    and analysis belongs to exactly one Project.
    """

    __tablename__ = "projects"

    # Primary identification
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Basic information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status and workflow
    status: Mapped[str] = mapped_column(
        String(50), default="created", index=True
    )  # created, active, processing, completed, failed, archived
    current_stage: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # initialization, data_acquisition, processing, analysis, reporting
    current_task: Mapped[str | None] = mapped_column(String(255), nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)

    # Geospatial metadata
    area_of_interest: Mapped[str | None] = mapped_column(Text, nullable=True)
    coordinate_system: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # EPSG code

    # Storage
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Tags and organization
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Flags
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Work state persistence
    completed_steps: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    pending_steps: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    last_opened_file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_viewed_map_position: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON {lat, lng, zoom}
    selected_layers: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    dashboard_layout: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    user_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Recovery tracking
    is_processing: Mapped[bool] = mapped_column(Boolean, default=False)
    last_job_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_job_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # running, completed, failed, interrupted

    # Versioning
    project_version: Mapped[str] = mapped_column(String(20), default="1.0.0")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"
