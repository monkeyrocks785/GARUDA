"""Database models for the Image Registration Engine."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class ImageRegistration(Base):
    """Stores image registration job metadata."""

    __tablename__ = "image_registrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Input files
    reference_path: Mapped[str] = mapped_column(Text)
    target_path: Mapped[str] = mapped_column(Text)
    output_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Registration configuration
    mode: Mapped[str] = mapped_column(String(50), default="automatic")
    feature_detector: Mapped[str] = mapped_column(String(50), default="orb")
    feature_matcher: Mapped[str] = mapped_column(String(50), default="bf")
    transform_type: Mapped[str] = mapped_column(String(50), default="affine")
    resampling: Mapped[str] = mapped_column(String(50), default="bilinear")

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reference image info
    ref_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ref_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ref_crs: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ref_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Target image info
    tgt_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tgt_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tgt_crs: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tgt_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Transformation matrix (JSON serialized)
    transform_matrix: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Quality metrics
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inlier_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inlier_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Pipeline integration
    pipeline_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )

    # Favorite/archive
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ControlPoint(Base):
    """Stores control points for manual registration."""

    __tablename__ = "control_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    registration_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("image_registrations.id", ondelete="CASCADE"), index=True
    )

    # Point index
    point_index: Mapped[int] = mapped_column(Integer)

    # Reference coordinates (pixel)
    ref_x: Mapped[float] = mapped_column(Float)
    ref_y: Mapped[float] = mapped_column(Float)

    # Target coordinates (pixel)
    target_x: Mapped[float] = mapped_column(Float)
    target_y: Mapped[float] = mapped_column(Float)

    # Geographic coordinates (optional)
    ref_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_lat: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Quality
    residual: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_inlier: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class RegistrationHistory(Base):
    """Tracks registration operation history."""

    __tablename__ = "registration_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    registration_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("image_registrations.id", ondelete="CASCADE"), index=True
    )

    operation: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    parameters: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RegistrationMetrics(Base):
    """Stores detailed quality metrics for registrations."""

    __tablename__ = "registration_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    registration_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("image_registrations.id", ondelete="CASCADE"), index=True
    )

    # Feature detection metrics
    features_detected_ref: Mapped[int | None] = mapped_column(Integer, nullable=True)
    features_detected_tgt: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Matching metrics
    raw_matches: Mapped[int | None] = mapped_column(Integer, nullable=True)
    good_matches: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inlier_matches: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Transform quality
    transform_determinant: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_residual: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_residual: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Overall
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_grade: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Raw metrics JSON
    raw_metrics: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
