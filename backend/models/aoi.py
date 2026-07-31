"""AOI (Area of Interest) model for GARUDA."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class AOI(Base):
    """Area of Interest entity.

    Represents a geographic area defined by the user for analysis.
    Each AOI belongs to exactly one Project.
    """

    __tablename__ = "aois"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Geometry stored as GeoJSON
    geometry: Mapped[str] = mapped_column(Text, nullable=False)
    geometry_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Polygon, MultiPolygon, etc.

    # Bounding box [min_lng, min_lat, max_lng, max_lat]
    bbox: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Area in square meters (calculated)
    area_m2: Mapped[float | None] = mapped_column(nullable=True)

    # Visual properties
    fill_color: Mapped[str] = mapped_column(String(20), default="#3388ff")
    fill_opacity: Mapped[float] = mapped_column(default=0.2)
    stroke_color: Mapped[str] = mapped_column(String(20), default="#3388ff")
    stroke_width: Mapped[float] = mapped_column(default=2.0)

    # Metadata
    source: Mapped[str] = mapped_column(
        String(50), default="manual"
    )  # manual, kml, geojson, shapefile
    source_file: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<AOI(id={self.id}, name={self.name}, type={self.geometry_type})>"
