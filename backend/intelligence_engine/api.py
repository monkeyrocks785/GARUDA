"""API endpoints for the Intelligence Analysis Engine."""

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from intelligence_engine.config import (
    DEVICE_TYPES,
    EXPORT_FORMATS,
    REVIEW_STATUS,
    TASK_TYPES,
)
from intelligence_engine.database.models import AnalysisJob, Detection, RegisteredModel
from intelligence_engine.postprocessing import detections_to_geojson
from intelligence_engine.services.analysis_service import AnalysisService
from intelligence_engine.services.inference_service import InferenceService
from intelligence_engine.services.model_registry import ModelRegistry
from intelligence_engine.services.review_service import ReviewService

router = APIRouter(prefix="/intelligence", tags=["Intelligence Analysis"])


# ── Pydantic Schemas ─────────────────────────────────────────────────────────

class ModelRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    task: str = Field(..., description="Task type: detection, segmentation, classification, etc.")
    version: str = Field(default="1.0.0")
    description: str | None = None
    author: str | None = None
    license: str | None = None
    framework: str = Field(default="pytorch")
    input_type: str = Field(default="raster")
    output_type: str = Field(default="detections")
    weights_path: str | None = None
    class_names: list[str] | None = None
    default_params: dict | None = None
    config: dict | None = None
    gpu_required: bool = Field(default=False)


class ModelResponse(BaseModel):
    id: str
    name: str
    version: str
    task: str
    description: str | None = None
    author: str | None = None
    license: str | None = None
    framework: str
    input_type: str
    output_type: str
    weights_path: str | None = None
    status: str
    is_loaded: bool
    gpu_required: bool
    class_names_json: str | None = None
    default_params_json: str | None = None
    error_message: str | None = None
    last_loaded_at: str | None = None
    inference_count: int
    favorite: bool
    archived: bool
    created_at: str | None = None
    modified_at: str | None = None


class AnalysisJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    model_id: str
    input_path: str
    description: str | None = None
    task_type: str = Field(default="detection")
    input_type: str = Field(default="raster")
    tile_size: int = Field(default=512, ge=64, le=4096)
    tile_overlap: int = Field(default=64, ge=0, le=512)
    batch_size: int = Field(default=8, ge=1, le=64)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    device: str = Field(default="cpu")
    parameters: dict | None = None


class AnalysisJobResponse(BaseModel):
    id: str
    project_id: str
    model_id: str
    name: str
    description: str | None = None
    task_type: str
    status: str
    input_path: str | None = None
    input_type: str | None = None
    output_path: str | None = None
    progress: float
    total_items: int
    processed_items: int
    detection_count: int
    execution_time_ms: int
    tile_size: int
    tile_overlap: int
    batch_size: int
    confidence_threshold: float
    iou_threshold: float
    device: str
    cancel_requested: bool
    error_message: str | None = None
    result_asset_id: str | None = None
    favorite: bool
    archived: bool
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str | None = None
    modified_at: str | None = None


class DetectionResponse(BaseModel):
    id: str
    job_id: str
    project_id: str
    model_id: str | None = None
    class_name: str
    class_id: int
    confidence: float
    geometry_json: str
    bbox_min_x: float
    bbox_min_y: float
    bbox_max_x: float
    bbox_max_y: float
    centroid_x: float
    centroid_y: float
    area: float
    model_version: str | None = None
    execution_time_ms: int
    tile_x: int | None = None
    tile_y: int | None = None
    review_status: str
    reviewer_notes: str | None = None
    reviewed_at: str | None = None
    reviewed_by: str | None = None
    edited_geometry_json: str | None = None
    created_at: str | None = None


class ReviewRequest(BaseModel):
    review_status: str = Field(..., description="accepted, rejected, uncertain, or pending")
    reviewer_notes: str | None = None
    reviewed_by: str | None = None


class BatchReviewRequest(BaseModel):
    detection_ids: list[str]
    review_status: str
    reviewer_notes: str | None = None
    reviewed_by: str | None = None


class DetectionEditGeometryRequest(BaseModel):
    geometry: dict


class DetectionNotesRequest(BaseModel):
    notes: str


# ── Model Endpoints ──────────────────────────────────────────────────────────

@router.get("/models/config")
def get_config():
    """Get available configuration options."""
    return {
        "task_types": TASK_TYPES,
        "device_types": DEVICE_TYPES,
        "review_status": REVIEW_STATUS,
        "export_formats": EXPORT_FORMATS,
    }


@router.post("/models", response_model=ModelResponse, status_code=201)
def register_model(data: ModelRegisterRequest, db: Session = Depends(get_db)):
    """Register a new AI model."""
    try:
        model = ModelRegistry.register_model(
            db=db,
            name=data.name,
            task=data.task,
            version=data.version,
            description=data.description,
            author=data.author,
            license=data.license,
            framework=data.framework,
            input_type=data.input_type,
            output_type=data.output_type,
            weights_path=data.weights_path,
            class_names=data.class_names,
            default_params=data.default_params,
            config=data.config,
            gpu_required=data.gpu_required,
        )
        return ModelResponse(**ModelRegistry.to_dict(model))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models", response_model=list[ModelResponse])
def list_models(
    task: str | None = Query(None),
    status: str | None = Query(None),
    loaded_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List all registered models."""
    models = ModelRegistry.list_models(db, task=task, status=status, loaded_only=loaded_only)
    return [ModelResponse(**ModelRegistry.to_dict(m)) for m in models]


@router.get("/models/{model_id}", response_model=ModelResponse)
def get_model(model_id: str, db: Session = Depends(get_db)):
    """Get a specific model."""
    model = ModelRegistry.get_model(db, model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelResponse(**ModelRegistry.to_dict(model))


@router.post("/models/{model_id}/load", response_model=ModelResponse)
def load_model(model_id: str, db: Session = Depends(get_db)):
    """Load a model into memory."""
    try:
        model = ModelRegistry.load_model(db, model_id)
        return ModelResponse(**ModelRegistry.to_dict(model))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/{model_id}/unload", response_model=ModelResponse)
def unload_model(model_id: str, db: Session = Depends(get_db)):
    """Unload a model from memory."""
    try:
        model = ModelRegistry.unload_model(db, model_id)
        return ModelResponse(**ModelRegistry.to_dict(model))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/models/{model_id}", status_code=204)
def delete_model(model_id: str, db: Session = Depends(get_db)):
    """Delete a model registration."""
    try:
        ModelRegistry.delete_model(db, model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/models/{model_id}/favorite")
def toggle_model_favorite(model_id: str, db: Session = Depends(get_db)):
    """Toggle model favorite status."""
    model = ModelRegistry.get_model(db, model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    model.favorite = not model.favorite
    db.commit()
    return {"id": model.id, "favorite": model.favorite}


# ── Analysis Job Endpoints ───────────────────────────────────────────────────

@router.post(
    "/project/{project_id}/jobs",
    response_model=AnalysisJobResponse,
    status_code=201,
)
def create_analysis_job(
    project_id: str,
    data: AnalysisJobCreate,
    db: Session = Depends(get_db),
):
    """Create a new analysis job."""
    try:
        job = AnalysisService.create_job(
            db=db,
            project_id=project_id,
            model_id=data.model_id,
            name=data.name,
            input_path=data.input_path,
            description=data.description,
            task_type=data.task_type,
            input_type=data.input_type,
            tile_size=data.tile_size,
            tile_overlap=data.tile_overlap,
            batch_size=data.batch_size,
            confidence_threshold=data.confidence_threshold,
            iou_threshold=data.iou_threshold,
            device=data.device,
            parameters=data.parameters,
        )
        return AnalysisJobResponse(**AnalysisService.to_dict(job))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/project/{project_id}/jobs",
    response_model=list[AnalysisJobResponse],
)
def list_analysis_jobs(
    project_id: str,
    status: str | None = Query(None),
    task_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List analysis jobs for a project."""
    jobs = AnalysisService.list_jobs(db, project_id=project_id, status=status, task_type=task_type)
    return [AnalysisJobResponse(**AnalysisService.to_dict(j)) for j in jobs]


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse)
def get_analysis_job(job_id: str, db: Session = Depends(get_db)):
    """Get a specific analysis job."""
    job = AnalysisService.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return AnalysisJobResponse(**AnalysisService.to_dict(job))


@router.post("/jobs/{job_id}/run", response_model=AnalysisJobResponse)
def run_analysis_job(job_id: str, db: Session = Depends(get_db)):
    """Execute an analysis job."""
    try:
        job = AnalysisService.run_job(db, job_id)
        return AnalysisJobResponse(**AnalysisService.to_dict(job))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/{job_id}/cancel", response_model=AnalysisJobResponse)
def cancel_analysis_job(job_id: str, db: Session = Depends(get_db)):
    """Request cancellation of a running job."""
    try:
        job = InferenceService.cancel_job(db, job_id)
        return AnalysisJobResponse(**AnalysisService.to_dict(job))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/jobs/{job_id}", status_code=204)
def delete_analysis_job(job_id: str, db: Session = Depends(get_db)):
    """Delete an analysis job and its detections."""
    try:
        AnalysisService.delete_job(db, job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{job_id}/history")
def get_job_history(job_id: str, db: Session = Depends(get_db)):
    """Get history for an analysis job."""
    history = AnalysisService.get_job_history(db, job_id)
    return [h.to_dict() for h in history]


# ── Detection Endpoints ──────────────────────────────────────────────────────

@router.get("/jobs/{job_id}/detections", response_model=list[DetectionResponse])
def list_job_detections(
    job_id: str,
    class_name: str | None = Query(None),
    review_status: str | None = Query(None),
    min_confidence: float | None = Query(None),
    db: Session = Depends(get_db),
):
    """List detections for a job."""
    detections = AnalysisService.get_job_detections(
        db, job_id, class_name=class_name,
        review_status=review_status, min_confidence=min_confidence,
    )
    return [DetectionResponse(**d.to_dict()) for d in detections]


@router.get("/jobs/{job_id}/detections/geojson")
def get_detections_geojson(
    job_id: str,
    class_name: str | None = Query(None),
    review_status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get detections as GeoJSON FeatureCollection."""
    detections = AnalysisService.get_job_detections(
        db, job_id, class_name=class_name, review_status=review_status,
    )
    det_dicts = [d.to_dict() for d in detections]
    return detections_to_geojson(det_dicts)


@router.get("/project/{project_id}/detections", response_model=list[DetectionResponse])
def list_project_detections(
    project_id: str,
    class_name: str | None = Query(None),
    review_status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List all detections for a project."""
    detections = AnalysisService.get_project_detections(
        db, project_id, class_name=class_name, review_status=review_status,
    )
    return [DetectionResponse(**d.to_dict()) for d in detections]


@router.get("/project/{project_id}/detections/geojson")
def get_project_detections_geojson(
    project_id: str,
    class_name: str | None = Query(None),
    review_status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get all project detections as GeoJSON FeatureCollection."""
    detections = AnalysisService.get_project_detections(
        db, project_id, class_name=class_name, review_status=review_status,
    )
    det_dicts = [d.to_dict() for d in detections]
    return detections_to_geojson(det_dicts)


@router.get("/project/{project_id}/review-stats")
def get_project_review_stats(project_id: str, db: Session = Depends(get_db)):
    """Get review statistics for a project."""
    return ReviewService.get_project_review_stats(db, project_id)


@router.get("/jobs/{job_id}/review-stats")
def get_job_review_stats(job_id: str, db: Session = Depends(get_db)):
    """Get review statistics for a job."""
    return ReviewService.get_review_stats(db, job_id)


# ── Review Endpoints ─────────────────────────────────────────────────────────

@router.patch("/detections/{detection_id}/review", response_model=DetectionResponse)
def review_detection(
    detection_id: str,
    data: ReviewRequest,
    db: Session = Depends(get_db),
):
    """Set review status on a detection."""
    try:
        det = ReviewService.review_detection(
            db, detection_id, data.review_status,
            data.reviewer_notes, data.reviewed_by,
        )
        return DetectionResponse(**det.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/detections/batch-review", response_model=list[DetectionResponse])
def batch_review_detections(
    data: BatchReviewRequest,
    db: Session = Depends(get_db),
):
    """Review multiple detections at once."""
    try:
        detections = ReviewService.batch_review(
            db, data.detection_ids, data.review_status,
            data.reviewer_notes, data.reviewed_by,
        )
        return [DetectionResponse(**d.to_dict()) for d in detections]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/detections/{detection_id}/notes", response_model=DetectionResponse)
def add_detection_notes(
    detection_id: str,
    data: DetectionNotesRequest,
    db: Session = Depends(get_db),
):
    """Add notes to a detection."""
    try:
        det = ReviewService.add_notes(db, detection_id, data.notes)
        return DetectionResponse(**det.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/detections/{detection_id}/geometry", response_model=DetectionResponse)
def edit_detection_geometry(
    detection_id: str,
    data: DetectionEditGeometryRequest,
    db: Session = Depends(get_db),
):
    """Edit detection geometry."""
    try:
        det = ReviewService.edit_geometry(db, detection_id, data.geometry)
        return DetectionResponse(**det.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
