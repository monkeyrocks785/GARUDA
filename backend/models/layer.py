"""Layer model for GARUDA map system."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class Layer(Base):
    """Map layer entity.

    Represents a layer in the map visualization.
    Each layer belongs to exactly one Project.
    """

    __tablename__ = "layers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    # Layer information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    layer_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # aoi, vector, raster, drawing, temporary, satellite, ai

    # Visibility and display
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    opacity: Mapped[float] = mapped_column(Float, default=1.0)
    z_index: Mapped[int] = mapped_column(Integer, default=0)

    # Source reference
    source_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )  # Reference to AOI, imported file, etc.
    source_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # aoi, imported_file, asset, raster_metadata, etc.

    # Coordinate reference system (e.g., EPSG:4326)
    crs: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Style properties (JSON)
    style: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata (renamed from 'metadata' which is reserved in SQLAlchemy)
    extra_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Layer(id={self.id}, name={self.name}, type={self.layer_type})>"
