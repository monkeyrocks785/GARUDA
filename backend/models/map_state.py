"""ProjectMapState model for GARUDA map persistence."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class ProjectMapState(Base):
    """Project map state entity.

    Stores the map visualization state for a project.
    Automatically restores when reopening the project.
    """

    __tablename__ = "project_map_states"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )

    # Map view state
    zoom: Mapped[float] = mapped_column(Float, default=2.0)
    center_lat: Mapped[float] = mapped_column(Float, default=20.0)
    center_lng: Mapped[float] = mapped_column(Float, default=0.0)
    map_rotation: Mapped[float] = mapped_column(Float, default=0.0)

    # Active basemap
    basemap: Mapped[str] = mapped_column(
        String(100), default="osm"
    )  # osm, esri_satellite, esri_terrain, etc.

    # Layer visibility state (JSON)
    visible_layers: Mapped[str | None] = mapped_column(Text, nullable=True)
    selected_layer_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )

    # UI state
    sidebar_width: Mapped[int] = mapped_column(default=280)
    panel_visible: Mapped[bool] = mapped_column(default=True)
    active_tool: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # pan, draw_polygon, measure_distance, etc.

    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<ProjectMapState(project_id={self.project_id}, zoom={self.zoom})>"
