"""ImportedFile model for GARUDA file management."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class ImportedFile(Base):
    """Imported file entity.

    Tracks files imported into the project (KML, GeoJSON, Shapefile).
    Each file belongs to exactly one Project.
    """

    __tablename__ = "imported_files"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    # File information
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # kml, geojson, shapefile
    file_size: Mapped[int] = mapped_column(Integer, default=0)

    # Storage
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Geometry information
    geometry_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    feature_count: Mapped[int] = mapped_column(Integer, default=0)

    # Validation status
    is_valid: Mapped[bool] = mapped_column(default=True)
    validation_errors: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Associated layer
    layer_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )  # Reference to created layer

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ImportedFile(id={self.id}, filename={self.filename}, type={self.file_type})>"
