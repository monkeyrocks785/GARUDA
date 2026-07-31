"""Database models for the Raster Processing Engine."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class RasterMetadata(Base):
    """Stores metadata extracted from raster files."""

    __tablename__ = "raster_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    # File path
    file_path: Mapped[str] = mapped_column(Text)

    # Raster info
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    band_count: Mapped[int] = mapped_column(Integer)
    data_type: Mapped[str] = mapped_column(String(50))
    nodata_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    crs: Mapped[str] = mapped_column(String(100))
    resolution_x: Mapped[float] = mapped_column(Float)
    resolution_y: Mapped[float] = mapped_column(Float)
    pixel_size_x: Mapped[float] = mapped_column(Float)
    pixel_size_y: Mapped[float] = mapped_column(Float)

    # Bounds (EPSG:4326)
    bounds_min_x: Mapped[float] = mapped_column(Float)
    bounds_min_y: Mapped[float] = mapped_column(Float)
    bounds_max_x: Mapped[float] = mapped_column(Float)
    bounds_max_y: Mapped[float] = mapped_column(Float)

    # Affine transform (6 values as JSON)
    transform: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Band info (JSON array of band details)
    bands_info: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Compression and format info
    compression: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_format: Mapped[str] = mapped_column(String(50))
    file_size: Mapped[int] = mapped_column(Integer)

    # Processing flags
    has_overviews: Mapped[bool] = mapped_column(Boolean, default=False)
    overview_levels: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Statistics (JSON)
    statistics: Mapped[str | None] = mapped_column(Text, nullable=True)
    histogram: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class RasterProcessingHistory(Base):
    """Tracks all raster processing operations."""

    __tablename__ = "raster_processing_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )

    operation: Mapped[str] = mapped_column(String(100))
    parameters: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    input_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # References the pipeline node if executed through pipeline
    pipeline_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    node_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RasterDerivedProduct(Base):
    """Tracks derived raster products (clipped, reprojected, etc.)."""

    __tablename__ = "raster_derived_products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    asset_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )

    operation: Mapped[str] = mapped_column(String(100))
    output_path: Mapped[str] = mapped_column(Text)
    output_filename: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer)

    # Parameters used to create this product
    parameters: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
