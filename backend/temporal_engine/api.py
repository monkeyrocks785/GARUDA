"""Temporal Engine - API Endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from temporal_engine.services import TemporalService

router = APIRouter(prefix="/timelines", tags=["Timelines"])


# --- Pydantic Schemas ---

class TimelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    project_id: str | None = None
    description: str | None = None
    group_by: str = "date"
    sort_order: str = "asc"
    tags: list[str] | None = None
    notes: str | None = None


class TimelineUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    group_by: str | None = None
    sort_order: str | None = None
    tags: list[str] | None = None
    notes: str | None = None


class TimelineResponse(BaseModel):
    id: str
    project_id: str | None = None
    name: str
    description: str | None = None
    group_by: str
    sort_order: str
    entry_count: int
    favorite: bool
    archived: bool
    tags: str | None = None
    notes: str | None = None
    storage_path: str | None = None
    created_at: datetime
    modified_at: datetime

    class Config:
        from_attributes = True


class EntryCreate(BaseModel):
    dataset_id: str
    acquisition_date: datetime | None = None
    acquisition_time: str | None = None
    sensor_name: str | None = None
    source: str | None = None
    resolution: str | None = None
    mission_id: str | None = None
    aoi_id: str | None = None
    dataset_type: str | None = None
    notes: str | None = None


class EntryUpdate(BaseModel):
    acquisition_date: datetime | None = None
    acquisition_time: str | None = None
    sensor_name: str | None = None
    source: str | None = None
    resolution: str | None = None
    visibility: bool | None = None
    opacity: float | None = None
    notes: str | None = None


class EntryResponse(BaseModel):
    id: str
    timeline_id: str
    dataset_id: str
    acquisition_date: datetime | None = None
    acquisition_time: str | None = None
    sensor_name: str | None = None
    source: str | None = None
    resolution: str | None = None
    mission_id: str | None = None
    aoi_id: str | None = None
    dataset_type: str | None = None
    sort_order: int
    visibility: bool
    opacity: float
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ComparisonCreate(BaseModel):
    name: str | None = None
    mode: str = "side_by_side"
    left_entry_id: str | None = None
    right_entry_id: str | None = None


class ComparisonUpdate(BaseModel):
    name: str | None = None
    mode: str | None = None
    left_entry_id: str | None = None
    right_entry_id: str | None = None
    swipe_position: float | None = None
    opacity: float | None = None
    linked_pan_zoom: bool | None = None
    map_center_lat: float | None = None
    map_center_lng: float | None = None
    map_zoom: float | None = None


class ComparisonResponse(BaseModel):
    id: str
    timeline_id: str
    name: str | None = None
    mode: str
    left_entry_id: str | None = None
    right_entry_id: str | None = None
    swipe_position: float
    opacity: float
    linked_pan_zoom: bool
    map_center_lat: float | None = None
    map_center_lng: float | None = None
    map_zoom: float | None = None
    status: str
    created_at: datetime
    modified_at: datetime

    class Config:
        from_attributes = True


class BookmarkCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    entry_id: str | None = None
    bookmark_date: datetime | None = None
    color: str | None = None
    notes: str | None = None


class BookmarkResponse(BaseModel):
    id: str
    timeline_id: str
    entry_id: str | None = None
    label: str
    bookmark_date: datetime | None = None
    color: str | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class LogResponse(BaseModel):
    id: str
    timeline_id: str
    action: str
    details: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    timestamp: datetime

    class Config:
        from_attributes = True


class TimelineStatsResponse(BaseModel):
    total_timelines: int
    total_entries: int


class ReorderRequest(BaseModel):
    entry_ids: list[str]


# --- Timeline Endpoints ---

@router.post("", response_model=TimelineResponse, status_code=201)
async def create_timeline(request: TimelineCreate, db: Session = Depends(get_db)):
    service = TemporalService(db)
    timeline = service.create_timeline(
        name=request.name,
        project_id=request.project_id,
        description=request.description,
        group_by=request.group_by,
        sort_order=request.sort_order,
        tags=request.tags,
        notes=request.notes,
    )
    return TimelineResponse.model_validate(timeline)


@router.get("", response_model=dict)
async def list_timelines(
    project_id: str | None = Query(None),
    search: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    service = TemporalService(db)
    timelines, total = service.list_timelines(project_id, search, offset, limit)
    return {
        "timelines": [TimelineResponse.model_validate(t) for t in timelines],
        "total": total,
    }


@router.get("/stats", response_model=TimelineStatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    service = TemporalService(db)
    return TimelineStatsResponse(**service.get_stats())


@router.get("/{timeline_id}", response_model=TimelineResponse)
async def get_timeline(timeline_id: str, db: Session = Depends(get_db)):
    service = TemporalService(db)
    timeline = service.get_timeline(timeline_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return TimelineResponse.model_validate(timeline)


@router.put("/{timeline_id}", response_model=TimelineResponse)
async def update_timeline(
    timeline_id: str, request: TimelineUpdate, db: Session = Depends(get_db)
):
    service = TemporalService(db)
    data = request.model_dump(exclude_unset=True)
    timeline = service.update_timeline(timeline_id, **data)
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return TimelineResponse.model_validate(timeline)


@router.delete("/{timeline_id}")
async def delete_timeline(timeline_id: str, db: Session = Depends(get_db)):
    service = TemporalService(db)
    if not service.delete_timeline(timeline_id):
        raise HTTPException(status_code=404, detail="Timeline not found")
    return {"status": "deleted"}


@router.post("/{timeline_id}/duplicate", response_model=TimelineResponse, status_code=201)
async def duplicate_timeline(
    timeline_id: str,
    name: str | None = Query(None),
    db: Session = Depends(get_db),
):
    service = TemporalService(db)
    timeline = service.duplicate_timeline(timeline_id, name)
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return TimelineResponse.model_validate(timeline)


@router.post("/{timeline_id}/favorite", response_model=TimelineResponse)
async def toggle_favorite(timeline_id: str, db: Session = Depends(get_db)):
    service = TemporalService(db)
    timeline = service.toggle_favorite(timeline_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return TimelineResponse.model_validate(timeline)


# --- Entry Endpoints ---

@router.post("/{timeline_id}/entries", response_model=EntryResponse, status_code=201)
async def add_entry(
    timeline_id: str, request: EntryCreate, db: Session = Depends(get_db)
):
    service = TemporalService(db)
    entry = service.add_entry(
        timeline_id=timeline_id,
        dataset_id=request.dataset_id,
        acquisition_date=request.acquisition_date,
        acquisition_time=request.acquisition_time,
        sensor_name=request.sensor_name,
        source=request.source,
        resolution=request.resolution,
        mission_id=request.mission_id,
        aoi_id=request.aoi_id,
        dataset_type=request.dataset_type,
        notes=request.notes,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return EntryResponse.model_validate(entry)


@router.get("/{timeline_id}/entries", response_model=list[EntryResponse])
async def get_entries(
    timeline_id: str,
    sensor: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: Session = Depends(get_db),
):
    service = TemporalService(db)
    entries = service.get_entries(timeline_id, sensor, date_from, date_to)
    return [EntryResponse.model_validate(e) for e in entries]


@router.put("/{timeline_id}/entries/{entry_id}", response_model=EntryResponse)
async def update_entry(
    timeline_id: str,
    entry_id: str,
    request: EntryUpdate,
    db: Session = Depends(get_db),
):
    service = TemporalService(db)
    data = request.model_dump(exclude_unset=True)
    entry = service.update_entry(entry_id, **data)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return EntryResponse.model_validate(entry)


@router.delete("/{timeline_id}/entries/{entry_id}")
async def remove_entry(timeline_id: str, entry_id: str, db: Session = Depends(get_db)):
    service = TemporalService(db)
    if not service.remove_entry(timeline_id, entry_id):
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "removed"}


@router.post("/{timeline_id}/entries/reorder")
async def reorder_entries(
    timeline_id: str, request: ReorderRequest, db: Session = Depends(get_db)
):
    service = TemporalService(db)
    service.reorder_entries(timeline_id, request.entry_ids)
    return {"status": "reordered"}


@router.get("/{timeline_id}/sensors")
async def get_sensors(timeline_id: str, db: Session = Depends(get_db)):
    service = TemporalService(db)
    return {"sensors": service.get_sensors(timeline_id)}


# --- Comparison Endpoints ---

@router.post("/{timeline_id}/comparison", response_model=ComparisonResponse, status_code=201)
async def create_comparison(
    timeline_id: str, request: ComparisonCreate, db: Session = Depends(get_db)
):
    service = TemporalService(db)
    session = service.create_comparison(
        timeline_id=timeline_id,
        name=request.name,
        mode=request.mode,
        left_entry_id=request.left_entry_id,
        right_entry_id=request.right_entry_id,
    )
    if not session:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return ComparisonResponse.model_validate(session)


@router.get("/{timeline_id}/comparison/{session_id}", response_model=ComparisonResponse)
async def get_comparison(
    timeline_id: str, session_id: str, db: Session = Depends(get_db)
):
    service = TemporalService(db)
    session = service.get_comparison(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return ComparisonResponse.model_validate(session)


@router.put("/{timeline_id}/comparison/{session_id}", response_model=ComparisonResponse)
async def update_comparison(
    timeline_id: str,
    session_id: str,
    request: ComparisonUpdate,
    db: Session = Depends(get_db),
):
    service = TemporalService(db)
    data = request.model_dump(exclude_unset=True)
    session = service.update_comparison(session_id, **data)
    if not session:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return ComparisonResponse.model_validate(session)


# --- Bookmark Endpoints ---

@router.post("/{timeline_id}/bookmarks", response_model=BookmarkResponse, status_code=201)
async def add_bookmark(
    timeline_id: str, request: BookmarkCreate, db: Session = Depends(get_db)
):
    service = TemporalService(db)
    bookmark = service.add_bookmark(
        timeline_id=timeline_id,
        label=request.label,
        entry_id=request.entry_id,
        bookmark_date=request.bookmark_date,
        color=request.color,
        notes=request.notes,
    )
    if not bookmark:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return BookmarkResponse.model_validate(bookmark)


@router.get("/{timeline_id}/bookmarks", response_model=list[BookmarkResponse])
async def get_bookmarks(timeline_id: str, db: Session = Depends(get_db)):
    service = TemporalService(db)
    return [BookmarkResponse.model_validate(b) for b in service.get_bookmarks(timeline_id)]


@router.delete("/{timeline_id}/bookmarks/{bookmark_id}")
async def delete_bookmark(
    timeline_id: str, bookmark_id: str, db: Session = Depends(get_db)
):
    service = TemporalService(db)
    if not service.delete_bookmark(bookmark_id):
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"status": "deleted"}


# --- Log Endpoints ---

@router.get("/{timeline_id}/logs", response_model=list[LogResponse])
async def get_logs(
    timeline_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    service = TemporalService(db)
    return [LogResponse.model_validate(l) for l in service.get_logs(timeline_id, limit)]
