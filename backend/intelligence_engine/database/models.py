"""Database models for the Intelligence Analysis Engine."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class RegisteredModel(Base):
    """Tracks all AI models registered in the system."""

    __tablename__ = "registered_models"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    task: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    license: Mapped[str | None] = mapped_column(String(255), nullable=True)
    framework: Mapped[str] = mapped_column(String(50), default="pytorch")
    input_type: Mapped[str] = mapped_column(String(50), default="raster")
    output_type: Mapped[str] = mapped_column(String(50), default="detections")
    weights_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    weights_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="registered", index=True)
    is_loaded: Mapped[bool] = mapped_column(Boolean, default=False)
    gpu_required: Mapped[bool] = mapped_column(Boolean, default=False)
    class_names_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_params_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_loaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    inference_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "task": self.task,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "framework": self.framework,
            "input_type": self.input_type,
            "output_type": self.output_type,
            "weights_path": self.weights_path,
            "weights_checksum": self.weights_checksum,
            "config_json": self.config_json,
            "status": self.status,
            "is_loaded": self.is_loaded,
            "gpu_required": self.gpu_required,
            "class_names_json": self.class_names_json,
            "default_params_json": self.default_params_json,
            "error_message": self.error_message,
            "last_loaded_at": self.last_loaded_at.isoformat() if self.last_loaded_at else None,
            "inference_count": self.inference_count,
            "favorite": self.favorite,
            "archived": self.archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }


class AnalysisJob(Base):
    """Tracks analysis jobs submitted by users."""

    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    model_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("registered_models.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    input_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    output_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    processed_items: Mapped[int] = mapped_column(Integer, default=0)
    detection_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    tile_size: Mapped[int] = mapped_column(Integer, default=512)
    tile_overlap: Mapped[int] = mapped_column(Integer, default=64)
    batch_size: Mapped[int] = mapped_column(Integer, default=8)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.5)
    iou_threshold: Mapped[float] = mapped_column(Float, default=0.45)
    device: Mapped[str] = mapped_column(String(20), default="cpu")
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    resume_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_asset_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "model_id": self.model_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "status": self.status,
            "input_path": self.input_path,
            "input_type": self.input_type,
            "output_path": self.output_path,
            "parameters_json": self.parameters_json,
            "progress": self.progress,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "detection_count": self.detection_count,
            "execution_time_ms": self.execution_time_ms,
            "tile_size": self.tile_size,
            "tile_overlap": self.tile_overlap,
            "batch_size": self.batch_size,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "device": self.device,
            "cancel_requested": self.cancel_requested,
            "error_message": self.error_message,
            "result_asset_id": self.result_asset_id,
            "favorite": self.favorite,
            "archived": self.archived,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }


class Detection(Base):
    """Individual detection result from AI inference."""

    __tablename__ = "detections"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    model_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("registered_models.id", ondelete="SET NULL"), nullable=True
    )
    class_name: Mapped[str] = mapped_column(String(100), index=True)
    class_id: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, index=True)
    geometry_json: Mapped[str] = mapped_column(Text)
    bbox_min_x: Mapped[float] = mapped_column(Float)
    bbox_min_y: Mapped[float] = mapped_column(Float)
    bbox_max_x: Mapped[float] = mapped_column(Float)
    bbox_max_y: Mapped[float] = mapped_column(Float)
    centroid_x: Mapped[float] = mapped_column(Float)
    centroid_y: Mapped[float] = mapped_column(Float)
    area: Mapped[float] = mapped_column(Float, default=0.0)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    processing_params_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    tile_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tile_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    edited_geometry_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "project_id": self.project_id,
            "model_id": self.model_id,
            "class_name": self.class_name,
            "class_id": self.class_id,
            "confidence": self.confidence,
            "geometry_json": self.geometry_json,
            "bbox_min_x": self.bbox_min_x,
            "bbox_min_y": self.bbox_min_y,
            "bbox_max_x": self.bbox_max_x,
            "bbox_max_y": self.bbox_max_y,
            "centroid_x": self.centroid_x,
            "centroid_y": self.centroid_y,
            "area": self.area,
            "model_version": self.model_version,
            "execution_time_ms": self.execution_time_ms,
            "processing_params_json": self.processing_params_json,
            "tile_x": self.tile_x,
            "tile_y": self.tile_y,
            "review_status": self.review_status,
            "reviewer_notes": self.reviewer_notes,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewed_by": self.reviewed_by,
            "edited_geometry_json": self.edited_geometry_json,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnalysisHistory(Base):
    """Audit log for analysis operations."""

    __tablename__ = "analysis_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    job_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "action": self.action,
            "details": self.details,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
