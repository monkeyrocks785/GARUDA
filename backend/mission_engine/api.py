"""Mission Engine - API Endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from mission_engine.services import MissionService

router = APIRouter(prefix="/missions", tags=["Missions"])


# --- Pydantic Schemas ---

class MissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(None, max_length=50)
    description: str | None = None
    classification: str | None = Field(None, max_length=100)
    status: str = "planning"
    priority: str = "medium"
    created_by: str | None = None
    mission_start: datetime | None = None
    mission_end: datetime | None = None
    area_of_interest: str | None = None
    tags: list[str] | None = None
    notes: str | None = None


class MissionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    code: str | None = Field(None, max_length=50)
    description: str | None = None
    classification: str | None = Field(None, max_length=100)
    status: str | None = None
    priority: str | None = None
    created_by: str | None = None
    mission_start: datetime | None = None
    mission_end: datetime | None = None
    area_of_interest: str | None = None
    tags: list[str] | None = None
    notes: str | None = None


class MissionResponse(BaseModel):
    id: str
    name: str
    code: str | None = None
    description: str | None = None
    classification: str | None = None
    status: str
    priority: str
    created_by: str | None = None
    mission_start: datetime | None = None
    mission_end: datetime | None = None
    area_of_interest: str | None = None
    tags: str | None = None
    notes: str | None = None
    favorite: bool = False
    archived: bool = False
    project_count: int = 0
    dataset_count: int = 0
    pipeline_count: int = 0
    report_count: int = 0
    storage_path: str | None = None
    created_at: datetime
    modified_at: datetime

    class Config:
        from_attributes = True


class ProjectLinkRequest(BaseModel):
    project_id: str
    notes: str | None = None


class NoteCreate(BaseModel):
    title: str | None = None
    content: str | None = None
    author: str | None = None


class NoteResponse(BaseModel):
    id: str
    mission_id: str
    title: str | None = None
    content: str | None = None
    author: str | None = None
    created_at: datetime
    modified_at: datetime

    class Config:
        from_attributes = True


class ActivityResponse(BaseModel):
    id: str
    mission_id: str
    action: str
    details: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    performed_by: str | None = None
    timestamp: datetime

    class Config:
        from_attributes = True


class MissionStatsResponse(BaseModel):
    total: int
    planning: int
    active: int
    completed: int
    paused: int
    archived: int
    cancelled: int
    total_projects: int


# --- Endpoints ---

@router.post("", response_model=MissionResponse, status_code=201)
async def create_mission(request: MissionCreate, db: Session = Depends(get_db)):
    service = MissionService(db)
    mission = service.create_mission(
        name=request.name,
        code=request.code,
        description=request.description,
        classification=request.classification,
        status=request.status,
        priority=request.priority,
        created_by=request.created_by,
        mission_start=request.mission_start,
        mission_end=request.mission_end,
        area_of_interest=request.area_of_interest,
        tags=request.tags,
        notes=request.notes,
    )
    return MissionResponse.model_validate(mission)


@router.get("", response_model=dict)
async def list_missions(
    status: str | None = Query(None),
    priority: str | None = Query(None),
    search: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    service = MissionService(db)
    missions, total = service.list_missions(
        status=status,
        priority=priority,
        search=search,
        offset=offset,
        limit=limit,
    )
    return {
        "missions": [MissionResponse.model_validate(m) for m in missions],
        "total": total,
    }


@router.get("/stats", response_model=MissionStatsResponse)
async def get_mission_stats(db: Session = Depends(get_db)):
    service = MissionService(db)
    stats = service.get_mission_stats()
    return MissionStatsResponse(**stats)


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: str, db: Session = Depends(get_db)):
    service = MissionService(db)
    mission = service.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return MissionResponse.model_validate(mission)


@router.put("/{mission_id}", response_model=MissionResponse)
async def update_mission(
    mission_id: str,
    request: MissionUpdate,
    db: Session = Depends(get_db),
):
    service = MissionService(db)
    update_data = request.model_dump(exclude_unset=True)
    mission = service.update_mission(mission_id, **update_data)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return MissionResponse.model_validate(mission)


@router.delete("/{mission_id}")
async def delete_mission(mission_id: str, db: Session = Depends(get_db)):
    service = MissionService(db)
    if not service.delete_mission(mission_id):
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"status": "deleted"}


@router.post("/{mission_id}/archive", response_model=MissionResponse)
async def archive_mission(mission_id: str, db: Session = Depends(get_db)):
    service = MissionService(db)
    mission = service.archive_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return MissionResponse.model_validate(mission)


@router.post("/{mission_id}/favorite", response_model=MissionResponse)
async def toggle_favorite(mission_id: str, db: Session = Depends(get_db)):
    service = MissionService(db)
    mission = service.toggle_favorite(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return MissionResponse.model_validate(mission)


@router.post("/{mission_id}/project")
async def add_project(
    mission_id: str,
    request: ProjectLinkRequest,
    db: Session = Depends(get_db),
):
    service = MissionService(db)
    link = service.add_project(mission_id, request.project_id, request.notes)
    if not link:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"status": "linked", "mission_id": mission_id, "project_id": request.project_id}


@router.delete("/{mission_id}/project/{project_id}")
async def remove_project(
    mission_id: str,
    project_id: str,
    db: Session = Depends(get_db),
):
    service = MissionService(db)
    if not service.remove_project(mission_id, project_id):
        raise HTTPException(status_code=404, detail="Link not found")
    return {"status": "unlinked"}


@router.get("/{mission_id}/projects")
async def get_mission_projects(mission_id: str, db: Session = Depends(get_db)):
    service = MissionService(db)
    links = service.get_mission_projects(mission_id)
    return [{"mission_id": l.mission_id, "project_id": l.project_id, "added_at": l.added_at.isoformat(), "notes": l.notes} for l in links]


@router.get("/{mission_id}/timeline", response_model=list[ActivityResponse])
async def get_timeline(
    mission_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    service = MissionService(db)
    activities = service.get_timeline(mission_id, limit)
    return [ActivityResponse.model_validate(a) for a in activities]


@router.get("/{mission_id}/notes", response_model=list[NoteResponse])
async def get_notes(mission_id: str, db: Session = Depends(get_db)):
    service = MissionService(db)
    notes = service.get_notes(mission_id)
    return [NoteResponse.model_validate(n) for n in notes]


@router.post("/{mission_id}/notes", response_model=NoteResponse, status_code=201)
async def add_note(
    mission_id: str,
    request: NoteCreate,
    db: Session = Depends(get_db),
):
    service = MissionService(db)
    note = service.add_note(mission_id, request.title, request.content, request.author)
    if not note:
        raise HTTPException(status_code=404, detail="Mission not found")
    return NoteResponse.model_validate(note)
