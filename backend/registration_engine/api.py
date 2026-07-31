"""API endpoints for the Image Registration Engine."""


from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from registration_engine.config import (
    FEATURE_DETECTORS,
    FEATURE_MATCHERS,
    REGISTRATION_MODES,
    RESAMPLING_METHODS,
    TRANSFORM_TYPES,
)
from registration_engine.services.control_points import ControlPointService
from registration_engine.services.registration_service import RegistrationService

router = APIRouter(prefix="/registrations", tags=["Image Registration"])


# --- Pydantic Schemas ---


class RegistrationCreate(BaseModel):
    """Schema for creating a registration job."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    reference_path: str = Field(..., description="Path to reference image")
    target_path: str = Field(..., description="Path to target image")
    mode: str = Field(default="automatic")
    feature_detector: str = Field(default="orb")
    feature_matcher: str = Field(default="bf")
    transform_type: str = Field(default="affine")
    resampling: str = Field(default="bilinear")


class RegistrationResponse(BaseModel):
    """Schema for registration response."""
    id: str
    project_id: str
    name: str
    description: str | None = None
    reference_path: str
    target_path: str
    output_path: str | None = None
    mode: str
    feature_detector: str
    feature_matcher: str
    transform_type: str
    resampling: str
    status: str
    error_message: str | None = None
    ref_width: int | None = None
    ref_height: int | None = None
    ref_crs: str | None = None
    ref_resolution: str | None = None
    tgt_width: int | None = None
    tgt_height: int | None = None
    tgt_crs: str | None = None
    tgt_resolution: str | None = None
    transform_matrix: list | None = None
    rmse: float | None = None
    matched_points: int | None = None
    inlier_count: int | None = None
    inlier_ratio: float | None = None
    confidence_score: float | None = None
    pipeline_id: str | None = None
    favorite: bool = False
    archived: bool = False
    created_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None


class ControlPointCreate(BaseModel):
    """Schema for creating a control point."""
    ref_x: float
    ref_y: float
    target_x: float
    target_y: float
    ref_lon: float | None = None
    ref_lat: float | None = None
    target_lon: float | None = None
    target_lat: float | None = None
    label: str | None = None
    notes: str | None = None


class ControlPointMove(BaseModel):
    """Schema for moving a control point."""
    ref_x: float
    ref_y: float
    target_x: float
    target_y: float


class BulkControlPointsCreate(BaseModel):
    """Schema for bulk creating control points."""
    points: list[ControlPointCreate]


class ControlPointResponse(BaseModel):
    """Schema for control point response."""
    id: str
    registration_id: str
    point_index: int
    ref_x: float
    ref_y: float
    target_x: float
    target_y: float
    ref_lon: float | None = None
    ref_lat: float | None = None
    target_lon: float | None = None
    target_lat: float | None = None
    residual: float | None = None
    is_inlier: bool = True
    label: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class HistoryResponse(BaseModel):
    """Schema for registration history."""
    id: str
    registration_id: str
    operation: str
    status: str
    parameters: str | None = None
    error_message: str | None = None
    execution_time_ms: int | None = None
    created_at: str | None = None
    completed_at: str | None = None


class MetricsResponse(BaseModel):
    """Schema for registration metrics."""
    id: str
    registration_id: str
    features_detected_ref: int | None = None
    features_detected_tgt: int | None = None
    raw_matches: int | None = None
    good_matches: int | None = None
    inlier_matches: int | None = None
    transform_determinant: float | None = None
    max_residual: float | None = None
    median_residual: float | None = None
    overall_score: float | None = None
    quality_grade: str | None = None
    raw_metrics: str | None = None
    created_at: str | None = None


class RegistrationConfigResponse(BaseModel):
    """Schema for available registration configuration."""
    feature_detectors: dict
    feature_matchers: dict
    transform_types: dict
    resampling_methods: dict
    registration_modes: dict


# --- Endpoints ---


@router.get("/config", response_model=RegistrationConfigResponse)
def get_registration_config():
    """Get available registration configuration options."""
    return RegistrationConfigResponse(
        feature_detectors=FEATURE_DETECTORS,
        feature_matchers=FEATURE_MATCHERS,
        transform_types=TRANSFORM_TYPES,
        resampling_methods=RESAMPLING_METHODS,
        registration_modes=REGISTRATION_MODES,
    )


@router.post(
    "/project/{project_id}",
    response_model=RegistrationResponse,
    status_code=201,
)
def create_registration(
    project_id: str,
    data: RegistrationCreate,
    db: Session = Depends(get_db),
):
    """Create a new image registration job."""
    try:
        reg = RegistrationService.create_registration(
            db=db,
            project_id=project_id,
            name=data.name,
            reference_path=data.reference_path,
            target_path=data.target_path,
            description=data.description,
            mode=data.mode,
            feature_detector=data.feature_detector,
            feature_matcher=data.feature_matcher,
            transform_type=data.transform_type,
            resampling=data.resampling,
        )
        return RegistrationResponse(**RegistrationService.to_dict(reg))
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/project/{project_id}",
    response_model=list[RegistrationResponse],
)
def list_registrations(
    project_id: str,
    status: str | None = Query(None),
    favorite: bool | None = Query(None),
    archived: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List all registrations for a project."""
    regs = RegistrationService.list_registrations(
        db, project_id, status=status, favorite=favorite, archived=archived
    )
    return [RegistrationResponse(**RegistrationService.to_dict(r)) for r in regs]


@router.get(
    "/project/{project_id}/history",
    response_model=list[HistoryResponse],
)
def list_all_history(
    project_id: str,
    db: Session = Depends(get_db),
):
    """List registration history for all registrations in a project."""
    from registration_engine.database.models import ImageRegistration, RegistrationHistory
    regs = (
        db.query(ImageRegistration)
        .filter(ImageRegistration.project_id == project_id)
        .all()
    )
    reg_ids = [r.id for r in regs]
    if not reg_ids:
        return []
    history = (
        db.query(RegistrationHistory)
        .filter(RegistrationHistory.registration_id.in_(reg_ids))
        .order_by(RegistrationHistory.created_at.desc())
        .all()
    )
    return [
        HistoryResponse(
            id=h.id,
            registration_id=h.registration_id,
            operation=h.operation,
            status=h.status,
            parameters=h.parameters,
            error_message=h.error_message,
            execution_time_ms=h.execution_time_ms,
            created_at=h.created_at.isoformat() if h.created_at else None,
            completed_at=h.completed_at.isoformat() if h.completed_at else None,
        )
        for h in history
    ]


@router.get("/{registration_id}", response_model=RegistrationResponse)
def get_registration(
    registration_id: str,
    db: Session = Depends(get_db),
):
    """Get a registration by ID."""
    reg = RegistrationService.get_registration(db, registration_id)
    if reg is None:
        raise HTTPException(status_code=404, detail="Registration not found")
    return RegistrationResponse(**RegistrationService.to_dict(reg))


@router.post("/{registration_id}/run")
def run_registration(
    registration_id: str,
    db: Session = Depends(get_db),
):
    """Run an automatic registration."""
    reg = RegistrationService.get_registration(db, registration_id)
    if reg is None:
        raise HTTPException(status_code=404, detail="Registration not found")

    if reg.mode == "manual":
        reg = RegistrationService.run_manual_registration(db, registration_id)
    else:
        reg = RegistrationService.run_automatic_registration(db, registration_id)

    return RegistrationResponse(**RegistrationService.to_dict(reg))


@router.post("/{registration_id}/run-manual")
def run_manual_registration(
    registration_id: str,
    resampling: str = Query("bilinear"),
    db: Session = Depends(get_db),
):
    """Run registration using manual control points."""
    reg = RegistrationService.get_registration(db, registration_id)
    if reg is None:
        raise HTTPException(status_code=404, detail="Registration not found")

    reg = RegistrationService.run_manual_registration(
        db, registration_id, resampling
    )
    return RegistrationResponse(**RegistrationService.to_dict(reg))


@router.delete("/{registration_id}", status_code=204)
def delete_registration(
    registration_id: str,
    db: Session = Depends(get_db),
):
    """Delete a registration and all associated data."""
    deleted = RegistrationService.delete_registration(db, registration_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Registration not found")
    return None


@router.patch("/{registration_id}/favorite")
def toggle_favorite(
    registration_id: str,
    db: Session = Depends(get_db),
):
    """Toggle favorite status."""
    reg = RegistrationService.toggle_favorite(db, registration_id)
    if reg is None:
        raise HTTPException(status_code=404, detail="Registration not found")
    return {"id": reg.id, "favorite": reg.favorite}


# --- Control Points ---


@router.get(
    "/{registration_id}/control-points",
    response_model=list[ControlPointResponse],
)
def list_control_points(
    registration_id: str,
    db: Session = Depends(get_db),
):
    """List all control points for a registration."""
    reg = RegistrationService.get_registration(db, registration_id)
    if reg is None:
        raise HTTPException(status_code=404, detail="Registration not found")

    points = ControlPointService.get_control_points(db, registration_id)
    return [ControlPointResponse(**ControlPointService.to_dict(p)) for p in points]


@router.post(
    "/{registration_id}/control-points",
    response_model=ControlPointResponse,
    status_code=201,
)
def create_control_point(
    registration_id: str,
    data: ControlPointCreate,
    db: Session = Depends(get_db),
):
    """Add a control point to a registration."""
    try:
        cp = ControlPointService.add_control_point(
            db=db,
            registration_id=registration_id,
            ref_x=data.ref_x,
            ref_y=data.ref_y,
            target_x=data.target_x,
            target_y=data.target_y,
            ref_lon=data.ref_lon,
            ref_lat=data.ref_lat,
            target_lon=data.target_lon,
            target_lat=data.target_lat,
            label=data.label,
            notes=data.notes,
        )
        return ControlPointResponse(**ControlPointService.to_dict(cp))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{registration_id}/control-points/bulk",
    response_model=list[ControlPointResponse],
    status_code=201,
)
def bulk_create_control_points(
    registration_id: str,
    data: BulkControlPointsCreate,
    db: Session = Depends(get_db),
):
    """Bulk add control points."""
    try:
        points_data = [
            {
                "ref_x": p.ref_x,
                "ref_y": p.ref_y,
                "target_x": p.target_x,
                "target_y": p.target_y,
                "ref_lon": p.ref_lon,
                "ref_lat": p.ref_lat,
                "target_lon": p.target_lon,
                "target_lat": p.target_lat,
                "label": p.label,
                "notes": p.notes,
            }
            for p in data.points
        ]
        points = ControlPointService.add_multiple_control_points(
            db, registration_id, points_data
        )
        return [ControlPointResponse(**ControlPointService.to_dict(p)) for p in points]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{registration_id}/control-points/{point_id}",
    response_model=ControlPointResponse,
)
def move_control_point(
    registration_id: str,
    point_id: str,
    data: ControlPointMove,
    db: Session = Depends(get_db),
):
    """Move a control point to new coordinates."""
    try:
        cp = ControlPointService.move_control_point(
            db=db,
            point_id=point_id,
            registration_id=registration_id,
            ref_x=data.ref_x,
            ref_y=data.ref_y,
            target_x=data.target_x,
            target_y=data.target_y,
        )
        return ControlPointResponse(**ControlPointService.to_dict(cp))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{registration_id}/control-points/{point_id}",
    status_code=204,
)
def delete_control_point(
    registration_id: str,
    point_id: str,
    db: Session = Depends(get_db),
):
    """Delete a control point."""
    deleted = ControlPointService.delete_control_point(db, point_id, registration_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Control point not found")
    return None


@router.delete(
    "/{registration_id}/control-points",
    status_code=204,
)
def delete_all_control_points(
    registration_id: str,
    db: Session = Depends(get_db),
):
    """Delete all control points for a registration."""
    count = ControlPointService.delete_all_control_points(db, registration_id)
    return {"deleted": count}


# --- History & Metrics ---


@router.get(
    "/{registration_id}/history",
    response_model=list[HistoryResponse],
)
def list_registration_history(
    registration_id: str,
    db: Session = Depends(get_db),
):
    """List history for a specific registration."""
    from registration_engine.database.models import RegistrationHistory
    history = (
        db.query(RegistrationHistory)
        .filter(RegistrationHistory.registration_id == registration_id)
        .order_by(RegistrationHistory.created_at.desc())
        .all()
    )
    return [
        HistoryResponse(
            id=h.id,
            registration_id=h.registration_id,
            operation=h.operation,
            status=h.status,
            parameters=h.parameters,
            error_message=h.error_message,
            execution_time_ms=h.execution_time_ms,
            created_at=h.created_at.isoformat() if h.created_at else None,
            completed_at=h.completed_at.isoformat() if h.completed_at else None,
        )
        for h in history
    ]


@router.get(
    "/{registration_id}/metrics",
    response_model=list[MetricsResponse],
)
def list_registration_metrics(
    registration_id: str,
    db: Session = Depends(get_db),
):
    """List metrics for a specific registration."""
    from registration_engine.database.models import RegistrationMetrics
    metrics = (
        db.query(RegistrationMetrics)
        .filter(RegistrationMetrics.registration_id == registration_id)
        .order_by(RegistrationMetrics.created_at.desc())
        .all()
    )
    return [
        MetricsResponse(
            id=m.id,
            registration_id=m.registration_id,
            features_detected_ref=m.features_detected_ref,
            features_detected_tgt=m.features_detected_tgt,
            raw_matches=m.raw_matches,
            good_matches=m.good_matches,
            inlier_matches=m.inlier_matches,
            transform_determinant=m.transform_determinant,
            max_residual=m.max_residual,
            median_residual=m.median_residual,
            overall_score=m.overall_score,
            quality_grade=m.quality_grade,
            raw_metrics=m.raw_metrics,
            created_at=m.created_at.isoformat() if m.created_at else None,
        )
        for m in metrics
    ]
