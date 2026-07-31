"""Project API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


# ============================================================
# Pydantic Schemas
# ============================================================


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: str | None = Field(None, description="Project description")
    area_of_interest: str | None = Field(None, description="Area of interest")
    coordinate_system: str | None = Field(None, description="EPSG code")
    tags: list[str] | None = Field(None, description="Project tags")


class ProjectUpdate(BaseModel):
    """Schema for updating project metadata."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    area_of_interest: str | None = None
    coordinate_system: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    last_opened_at: datetime | None = None


class WorkStateUpdate(BaseModel):
    """Schema for updating project work state."""

    current_stage: str | None = None
    current_task: str | None = None
    progress: float | None = Field(None, ge=0, le=100)
    completed_steps: list[str] | None = None
    pending_steps: list[str] | None = None
    last_opened_file: str | None = None
    last_viewed_map_position: dict | None = None
    selected_layers: list[str] | None = None
    dashboard_layout: dict | None = None
    user_notes: str | None = None


class ProjectResponse(BaseModel):
    """Schema for project response."""

    id: str
    name: str
    description: str | None
    status: str
    current_stage: str | None
    current_task: str | None
    progress: float
    area_of_interest: str | None
    coordinate_system: str | None
    storage_path: str
    tags: str | None
    notes: str | None
    favorite: bool
    archived: bool
    completed_steps: str | None
    pending_steps: str | None
    last_opened_file: str | None
    last_viewed_map_position: str | None
    selected_layers: str | None
    dashboard_layout: str | None
    user_notes: str | None
    is_processing: bool
    last_job_id: str | None
    last_job_status: str | None
    project_version: str
    created_at: datetime
    updated_at: datetime
    last_opened_at: datetime | None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for project list response."""

    projects: list[ProjectResponse]
    total: int
    offset: int
    limit: int


class ProjectStatsResponse(BaseModel):
    """Schema for project statistics."""

    total: int
    archived: int
    favorites: int
    processing: int


class RecoveryResponse(BaseModel):
    """Schema for recovery response."""

    recovered: list[ProjectResponse]
    count: int


# ============================================================
# Endpoints
# ============================================================


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Create a new project."""
    service = ProjectService(db)
    try:
        project = service.create_project(
            name=data.name,
            description=data.description,
            area_of_interest=data.area_of_interest,
            coordinate_system=data.coordinate_system,
            tags=data.tags,
        )
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    include_archived: bool = Query(False, description="Include archived projects"),
    search: str | None = Query(None, description="Search term"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    """List all projects with optional filters."""
    service = ProjectService(db)

    if search:
        projects = service.repository.search(
            search, include_archived=include_archived, limit=limit
        )
    else:
        projects = service.repository.get_all(
            include_archived=include_archived, limit=limit, offset=offset
        )

    total = service.repository.count(include_archived=include_archived)

    return ProjectListResponse(
        projects=projects,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/recent", response_model=list[ProjectResponse])
async def get_recent_projects(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[ProjectResponse]:
    """Get recently opened projects."""
    service = ProjectService(db)
    return service.repository.get_recent(limit=limit)


@router.get("/favorites", response_model=list[ProjectResponse])
async def get_favorite_projects(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ProjectResponse]:
    """Get favorite projects."""
    service = ProjectService(db)
    return service.repository.get_favorites(limit=limit)


@router.get("/stats", response_model=ProjectStatsResponse)
async def get_project_stats(
    db: Session = Depends(get_db),
) -> ProjectStatsResponse:
    """Get project statistics."""
    service = ProjectService(db)
    return service.get_project_stats()


@router.get("/recovery", response_model=RecoveryResponse)
async def check_for_recovery(
    db: Session = Depends(get_db),
) -> RecoveryResponse:
    """Check for projects that need recovery after crash."""
    service = ProjectService(db)
    recovered = service.recover_interrupted_projects()
    return RecoveryResponse(recovered=recovered, count=len(recovered))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Get a project by ID."""
    service = ProjectService(db)
    project = service.repository.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Update project metadata."""
    service = ProjectService(db)
    try:
        # Filter out None values
        updates = data.model_dump(exclude_none=True)
        project = service.update_metadata(project_id, **updates)
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{project_id}/work-state", response_model=ProjectResponse)
async def update_work_state(
    project_id: str,
    data: WorkStateUpdate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Update project work state (auto-saved)."""
    service = ProjectService(db)
    try:
        project = service.update_work_state(
            project_id,
            current_stage=data.current_stage,
            current_task=data.current_task,
            progress=data.progress,
            completed_steps=data.completed_steps,
            pending_steps=data.pending_steps,
            last_opened_file=data.last_opened_file,
            last_viewed_map_position=data.last_viewed_map_position,
            selected_layers=data.selected_layers,
            dashboard_layout=data.dashboard_layout,
            user_notes=data.user_notes,
        )
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    delete_files: bool = Query(True, description="Delete project files"),
    db: Session = Depends(get_db),
) -> None:
    """Delete a project."""
    service = ProjectService(db)
    try:
        service.delete_project(project_id, delete_files=delete_files)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Archive a project."""
    service = ProjectService(db)
    try:
        return service.archive_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/unarchive", response_model=ProjectResponse)
async def unarchive_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Unarchive a project."""
    service = ProjectService(db)
    try:
        return service.unarchive_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/favorite", response_model=ProjectResponse)
async def toggle_favorite(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Toggle favorite status."""
    service = ProjectService(db)
    try:
        return service.toggle_favorite(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/duplicate", response_model=ProjectResponse, status_code=201)
async def duplicate_project(
    project_id: str,
    new_name: str | None = Query(None, description="Name for the duplicate"),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Duplicate a project."""
    service = ProjectService(db)
    try:
        return service.duplicate_project(project_id, new_name=new_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/open", response_model=ProjectResponse)
async def open_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Open a project and update last opened timestamp."""
    service = ProjectService(db)
    try:
        return service.open_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
