"""Workspace State model - persists GIS workspace layout and tool state."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class WorkspaceState(Base):
    """Persisted workspace layout, tool state, and panel configuration."""

    __tablename__ = "workspace_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )

    # Map view
    zoom: Mapped[float] = mapped_column(Float, default=2.0)
    center_lat: Mapped[float] = mapped_column(Float, default=20.0)
    center_lng: Mapped[float] = mapped_column(Float, default=0.0)
    map_rotation: Mapped[float] = mapped_column(Float, default=0.0)
    basemap: Mapped[str] = mapped_column(String(50), default="osm")

    # Active tool
    active_tool: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Selected object
    selected_layer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    selected_object_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    selected_object_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Visible layers (JSON array of layer IDs)
    visible_layers: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Panel layout (JSON: { panelId: { visible: bool, width: number, position: string } })
    panel_layout: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Drawing features (JSON: GeoJSON FeatureCollection of drawn features)
    drawing_features: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Measurement features (JSON: array of measurement geometries)
    measurement_features: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Undo/redo stacks (JSON)
    undo_stack: Mapped[str | None] = mapped_column(Text, nullable=True)
    redo_stack: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
