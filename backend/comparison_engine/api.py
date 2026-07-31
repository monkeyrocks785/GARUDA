"""API endpoints for the Temporal Comparison Engine."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from comparison_engine.config import (
    ANNOTATION_COLORS,
    ANNOTATION_SHAPES,
    COMPARISON_MODES,
    DIFFERENCE_TYPES,
    EXPORT_FORMATS,
    EXPORT_SCOPES,
    MEASUREMENT_UNITS,
    PLAYBACK_SPEEDS,
    SYNC_OPTIONS,
)
from comparison_engine.services.annotation_service import AnnotationService
from comparison_engine.services.bookmark_service import BookmarkService
from comparison_engine.services.difference_service import DifferenceService
from comparison_engine.services.export_service import ExportService
from comparison_engine.services.measurement_service import MeasurementService
from comparison_engine.services.session_service import SessionService
from comparison_engine.services.sync_service import SyncService
from comparison_engine.services.timeline_service import TimelineService
from database.connection import get_db

router = APIRouter(prefix="/comparisons", tags=["Temporal Comparison"])


# --- Pydantic Schemas ---


class SessionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    dataset_paths: list[str] = Field(..., min_length=2)
    dataset_labels: list[str] | None = None
    mode: str = Field(default="side_by_side")


class SessionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    mode: str | None = None
    difference_type: str | None = None
    difference_threshold: float | None = None
    opacity: float | None = None
    swipe_position: float | None = None
    blink_interval_ms: int | None = None
    favorite: bool | None = None
    archived: bool | None = None


class SessionResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: str | None = None
    dataset_paths: list[str]
    dataset_labels: list[str]
    mode: str
    difference_type: str | None = None
    difference_threshold: float | None = None
    sync_options: list[str]
    timeline_position: int | None = None
    playback_speed: float | None = None
    is_playing: bool
    is_looping: bool
    layout_state: dict | None = None
    map_state: dict | None = None
    opacity: float
    swipe_position: float
    blink_interval_ms: int
    status: str
    error_message: str | None = None
    pipeline_id: str | None = None
    favorite: bool
    archived: bool
    created_at: str | None = None
    updated_at: str | None = None
    last_opened_at: str | None = None


class ViewResponse(BaseModel):
    id: str
    session_id: str
    view_index: int
    dataset_path: str
    dataset_label: str
    display_settings: dict | None = None
    visible: bool
    created_at: str | None = None
    updated_at: str | None = None


class BookmarkCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    timeline_position: int | None = None
    map_state: dict | None = None
    opacity: float | None = None
    swipe_position: float | None = None
    mode: str | None = None
    view_settings: dict | None = None


class BookmarkResponse(BaseModel):
    id: str
    session_id: str
    name: str
    description: str | None = None
    timeline_position: int | None = None
    map_state: dict | None = None
    opacity: float | None = None
    swipe_position: float | None = None
    mode: str | None = None
    view_settings: dict | None = None
    sort_order: int
    created_at: str | None = None


class AnnotationCreate(BaseModel):
    annotation_type: str
    geometry: dict
    label: str | None = None
    notes: str | None = None
    color: str = "#FF0000"
    stroke_width: int = 2
    fill_opacity: float = 0.3
    timeline_position: int | None = None
    view_index: int | None = None


class AnnotationResponse(BaseModel):
    id: str
    session_id: str
    annotation_type: str
    geometry: dict | None = None
    label: str | None = None
    notes: str | None = None
    color: str
    stroke_width: int
    fill_opacity: float
    timeline_position: int | None = None
    view_index: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ExportCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    export_format: str
    export_scope: str
    export_options: dict | None = None


class ExportResponse(BaseModel):
    id: str
    session_id: str
    name: str
    export_format: str
    export_scope: str
    output_path: str
    file_size: int | None = None
    export_options: dict | None = None
    status: str
    error_message: str | None = None
    created_at: str | None = None
    completed_at: str | None = None


class MeasurementCreate(BaseModel):
    measurement_type: str
    value: float
    geometry: dict
    unit: str = "pixels"
    label: str | None = None
    timeline_position: int | None = None


class MeasurementResponse(BaseModel):
    id: str
    session_id: str
    measurement_type: str
    unit: str
    value: float
    geometry: dict | None = None
    label: str | None = None
    timeline_position: int | None = None
    created_at: str | None = None


class DifferenceRequest(BaseModel):
    file_a: str
    file_b: str
    diff_type: str = "absolute"
    threshold: float = 0.1


class SyncOptionsUpdate(BaseModel):
    enabled: list[str]


class MapStateUpdate(BaseModel):
    center: list[float] | None = None
    zoom: float | None = None
    rotation: float | None = None


class ComparisonConfigResponse(BaseModel):
    modes: dict
    difference_types: dict
    sync_options: dict
    export_formats: dict
    export_scopes: dict
    annotation_shapes: dict
    annotation_colors: list
    measurement_units: dict
    playback_speeds: list


# --- Session Endpoints ---


@router.get("/config", response_model=ComparisonConfigResponse)
def get_comparison_config():
    """Get available comparison configuration options."""
    return ComparisonConfigResponse(
        modes=COMPARISON_MODES,
        difference_types=DIFFERENCE_TYPES,
        sync_options=SYNC_OPTIONS,
        export_formats=EXPORT_FORMATS,
        export_scopes=EXPORT_SCOPES,
        annotation_shapes=ANNOTATION_SHAPES,
        annotation_colors=ANNOTATION_COLORS,
        measurement_units=MEASUREMENT_UNITS,
        playback_speeds=PLAYBACK_SPEEDS,
    )


@router.post(
    "/project/{project_id}",
    response_model=SessionResponse,
    status_code=201,
)
def create_session(
    project_id: str,
    data: SessionCreate,
    db: Session = Depends(get_db),
):
    """Create a new comparison session."""
    try:
        session = SessionService.create_session(
            db=db,
            project_id=project_id,
            name=data.name,
            dataset_paths=data.dataset_paths,
            dataset_labels=data.dataset_labels,
            description=data.description,
            mode=data.mode,
        )
        return SessionResponse(**SessionService.to_dict(session))
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/project/{project_id}",
    response_model=list[SessionResponse],
)
def list_sessions(
    project_id: str,
    status: str | None = Query(None),
    favorite: bool | None = Query(None),
    archived: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List comparison sessions for a project."""
    sessions = SessionService.list_sessions(
        db, project_id, status=status, favorite=favorite, archived=archived
    )
    return [SessionResponse(**SessionService.to_dict(s)) for s in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Get a comparison session by ID."""
    session = SessionService.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**SessionService.to_dict(session))


@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: str,
    data: SessionUpdate,
    db: Session = Depends(get_db),
):
    """Update a comparison session."""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    session = SessionService.update_session(db, session_id, **update_data)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**SessionService.to_dict(session))


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Soft-delete a comparison session."""
    deleted = SessionService.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return None


@router.patch("/{session_id}/favorite")
def toggle_favorite(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Toggle favorite status."""
    session = SessionService.toggle_favorite(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"id": session.id, "favorite": session.favorite}


class ViewUpdate(BaseModel):
    display_settings: dict | None = None
    visible: bool | None = None
    dataset_label: str | None = None


# --- Views ---


@router.get(
    "/{session_id}/views",
    response_model=list[ViewResponse],
)
def list_views(
    session_id: str,
    db: Session = Depends(get_db),
):
    """List views for a session."""
    views = SessionService.get_views(db, session_id)
    return [ViewResponse(**SessionService.view_to_dict(v)) for v in views]


@router.patch(
    "/{session_id}/views/{view_id}",
    response_model=ViewResponse,
)
def update_view(
    session_id: str,
    view_id: str,
    data: ViewUpdate,
    db: Session = Depends(get_db),
):
    """Update a comparison view."""
    kwargs = {}
    if data.display_settings is not None:
        kwargs["display_settings"] = json.dumps(data.display_settings)
    if data.visible is not None:
        kwargs["visible"] = data.visible
    if data.dataset_label is not None:
        kwargs["dataset_label"] = data.dataset_label

    view = SessionService.update_view(db, view_id, session_id, **kwargs)
    if view is None:
        raise HTTPException(status_code=404, detail="View not found")
    return ViewResponse(**SessionService.view_to_dict(view))


# --- Timeline ---


@router.get("/{session_id}/timeline")
def get_timeline(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Get timeline state."""
    state = TimelineService.get_timeline_state(db, session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


@router.patch("/{session_id}/timeline/position")
def set_timeline_position(
    session_id: str,
    position: int = Query(..., ge=0),
    db: Session = Depends(get_db),
):
    """Set timeline position."""
    session = TimelineService.set_position(db, session_id, position)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"position": session.timeline_position}


@router.post("/{session_id}/timeline/previous")
def previous_date(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Go to previous date."""
    session = TimelineService.previous_date(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"position": session.timeline_position}


@router.post("/{session_id}/timeline/next")
def next_date(
    session_id: str,
    max_position: int = Query(1000, ge=0),
    db: Session = Depends(get_db),
):
    """Go to next date."""
    session = TimelineService.next_date(db, session_id, max_position)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"position": session.timeline_position}


@router.post("/{session_id}/timeline/jump")
def jump_to_date(
    session_id: str,
    position: int = Query(..., ge=0),
    db: Session = Depends(get_db),
):
    """Jump to a specific date."""
    session = TimelineService.jump_to_date(db, session_id, position)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"position": session.timeline_position}


@router.post("/{session_id}/timeline/play")
def start_playback(
    session_id: str,
    speed: float | None = Query(None),
    db: Session = Depends(get_db),
):
    """Start playback."""
    session = TimelineService.start_playback(db, session_id, speed)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"is_playing": session.is_playing, "playback_speed": session.playback_speed}


@router.post("/{session_id}/timeline/pause")
def pause_playback(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Pause playback."""
    session = TimelineService.pause_playback(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"is_playing": session.is_playing}


@router.patch("/{session_id}/timeline/loop")
def toggle_loop(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Toggle loop mode."""
    session = TimelineService.toggle_loop(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"is_looping": session.is_looping}


@router.patch("/{session_id}/timeline/speed")
def set_playback_speed(
    session_id: str,
    speed: float = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    """Set playback speed."""
    session = TimelineService.set_playback_speed(db, session_id, speed)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"playback_speed": session.playback_speed}


# --- Synchronization ---


@router.get("/{session_id}/sync")
def get_sync_options(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Get synchronization options."""
    options = SyncService.get_sync_options(db, session_id)
    if options is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return options


@router.patch("/{session_id}/sync")
def set_sync_options(
    session_id: str,
    data: SyncOptionsUpdate,
    db: Session = Depends(get_db),
):
    """Set synchronization options."""
    try:
        session = SyncService.set_sync_options(db, session_id, data.enabled)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"enabled": json.loads(session.sync_options)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{session_id}/sync/toggle/{option}")
def toggle_sync_option(
    session_id: str,
    option: str,
    db: Session = Depends(get_db),
):
    """Toggle a single sync option."""
    try:
        session = SyncService.toggle_sync_option(db, session_id, option)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"enabled": json.loads(session.sync_options)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/map-state")
def get_map_state(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Get synchronized map state."""
    state = SyncService.get_map_state(db, session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


@router.patch("/{session_id}/map-state")
def update_map_state(
    session_id: str,
    data: MapStateUpdate,
    db: Session = Depends(get_db),
):
    """Update synchronized map state."""
    session = SyncService.update_map_state(
        db, session_id,
        center=data.center,
        zoom=data.zoom,
        rotation=data.rotation,
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SyncService.get_map_state(db, session_id)


# --- Difference ---


@router.post("/difference/preview")
def generate_difference(
    data: DifferenceRequest,
):
    """Generate a difference visualization preview."""
    try:
        result = DifferenceService.generate_difference_preview(
            file_a=data.file_a,
            file_b=data.file_b,
            diff_type=data.diff_type,
            threshold=data.threshold,
        )
        return result
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Bookmarks ---


@router.get(
    "/{session_id}/bookmarks",
    response_model=list[BookmarkResponse],
)
def list_bookmarks(
    session_id: str,
    db: Session = Depends(get_db),
):
    """List bookmarks for a session."""
    bookmarks = BookmarkService.get_bookmarks(db, session_id)
    return [BookmarkResponse(**BookmarkService.to_dict(b)) for b in bookmarks]


@router.post(
    "/{session_id}/bookmarks",
    response_model=BookmarkResponse,
    status_code=201,
)
def create_bookmark(
    session_id: str,
    data: BookmarkCreate,
    db: Session = Depends(get_db),
):
    """Create a new bookmark."""
    try:
        bookmark = BookmarkService.create_bookmark(
            db=db,
            session_id=session_id,
            name=data.name,
            description=data.description,
            timeline_position=data.timeline_position,
            map_state=data.map_state,
            opacity=data.opacity,
            swipe_position=data.swipe_position,
            mode=data.mode,
            view_settings=data.view_settings,
        )
        return BookmarkResponse(**BookmarkService.to_dict(bookmark))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{session_id}/bookmarks/{bookmark_id}",
    status_code=204,
)
def delete_bookmark(
    session_id: str,
    bookmark_id: str,
    db: Session = Depends(get_db),
):
    """Delete a bookmark."""
    deleted = BookmarkService.delete_bookmark(db, bookmark_id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return None


# --- Annotations ---


@router.get(
    "/{session_id}/annotations",
    response_model=list[AnnotationResponse],
)
def list_annotations(
    session_id: str,
    annotation_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List annotations for a session."""
    annotations = AnnotationService.get_annotations(db, session_id, annotation_type)
    return [AnnotationResponse(**AnnotationService.to_dict(a)) for a in annotations]


@router.post(
    "/{session_id}/annotations",
    response_model=AnnotationResponse,
    status_code=201,
)
def create_annotation(
    session_id: str,
    data: AnnotationCreate,
    db: Session = Depends(get_db),
):
    """Create a new annotation."""
    try:
        annotation = AnnotationService.create_annotation(
            db=db,
            session_id=session_id,
            annotation_type=data.annotation_type,
            geometry=data.geometry,
            label=data.label,
            notes=data.notes,
            color=data.color,
            stroke_width=data.stroke_width,
            fill_opacity=data.fill_opacity,
            timeline_position=data.timeline_position,
            view_index=data.view_index,
        )
        return AnnotationResponse(**AnnotationService.to_dict(annotation))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{session_id}/annotations/{annotation_id}",
    status_code=204,
)
def delete_annotation(
    session_id: str,
    annotation_id: str,
    db: Session = Depends(get_db),
):
    """Delete an annotation."""
    deleted = AnnotationService.delete_annotation(db, annotation_id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return None


@router.delete(
    "/{session_id}/annotations",
    status_code=204,
)
def delete_all_annotations(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Delete all annotations for a session."""
    count = AnnotationService.delete_all_annotations(db, session_id)
    return {"deleted": count}


# --- Measurements ---


@router.get(
    "/{session_id}/measurements",
    response_model=list[MeasurementResponse],
)
def list_measurements(
    session_id: str,
    measurement_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """List measurements for a session."""
    measurements = MeasurementService.get_measurements(db, session_id, measurement_type)
    return [MeasurementResponse(**MeasurementService.to_dict(m)) for m in measurements]


@router.post(
    "/{session_id}/measurements",
    response_model=MeasurementResponse,
    status_code=201,
)
def create_measurement(
    session_id: str,
    data: MeasurementCreate,
    db: Session = Depends(get_db),
):
    """Create a new measurement."""
    try:
        measurement = MeasurementService.create_measurement(
            db=db,
            session_id=session_id,
            measurement_type=data.measurement_type,
            value=data.value,
            geometry=data.geometry,
            unit=data.unit,
            label=data.label,
            timeline_position=data.timeline_position,
        )
        return MeasurementResponse(**MeasurementService.to_dict(measurement))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{session_id}/measurements/{measurement_id}",
    status_code=204,
)
def delete_measurement(
    session_id: str,
    measurement_id: str,
    db: Session = Depends(get_db),
):
    """Delete a measurement."""
    deleted = MeasurementService.delete_measurement(db, measurement_id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return None


# --- Exports ---


@router.get(
    "/{session_id}/exports",
    response_model=list[ExportResponse],
)
def list_exports(
    session_id: str,
    db: Session = Depends(get_db),
):
    """List exports for a session."""
    exports = ExportService.list_exports(db, session_id)
    return [ExportResponse(**ExportService.to_dict(e)) for e in exports]


@router.post(
    "/{session_id}/exports",
    response_model=ExportResponse,
    status_code=201,
)
def create_export(
    session_id: str,
    data: ExportCreate,
    db: Session = Depends(get_db),
):
    """Create an export."""
    try:
        export = ExportService.create_export(
            db=db,
            session_id=session_id,
            name=data.name,
            export_format=data.export_format,
            export_scope=data.export_scope,
            export_options=data.export_options,
        )
        return ExportResponse(**ExportService.to_dict(export))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/exports/json")
def export_session_json(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Export session as JSON."""
    try:
        data = ExportService.export_session_json(db, session_id)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
