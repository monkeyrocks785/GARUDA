"""Workspace State API endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from models.workspace_state import WorkspaceState

router = APIRouter()


class WorkspaceStateResponse(BaseModel):
    """Schema for workspace state response."""

    id: str
    project_id: str
    zoom: float
    center_lat: float
    center_lng: float
    map_rotation: float
    basemap: str
    active_tool: str | None
    selected_layer_id: str | None
    selected_object_id: str | None
    selected_object_type: str | None
    visible_layers: str | None
    panel_layout: str | None
    drawing_features: str | None
    measurement_features: str | None
    undo_stack: str | None
    redo_stack: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceStateUpdate(BaseModel):
    """Schema for updating workspace state."""

    zoom: float | None = None
    center_lat: float | None = None
    center_lng: float | None = None
    map_rotation: float | None = None
    basemap: str | None = None
    active_tool: str | None = None
    selected_layer_id: str | None = None
    selected_object_id: str | None = None
    selected_object_type: str | None = None
    visible_layers: str | None = None
    panel_layout: str | None = None
    drawing_features: str | None = None
    measurement_features: str | None = None
    undo_stack: str | None = None
    redo_stack: str | None = None


def _get_or_create(db: Session, project_id: str) -> WorkspaceState:
    """Get or create workspace state for a project."""
    state = db.query(WorkspaceState).filter(
        WorkspaceState.project_id == project_id
    ).first()
    if not state:
        state = WorkspaceState(
            id=str(uuid.uuid4()),
            project_id=project_id,
            zoom=2.0,
            center_lat=20.0,
            center_lng=0.0,
            map_rotation=0.0,
            basemap="osm",
        )
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


@router.get(
    "/projects/{project_id}/workspace",
    response_model=WorkspaceStateResponse,
)
async def get_workspace_state(
    project_id: str,
    db: Session = Depends(get_db),
) -> WorkspaceStateResponse:
    """Get workspace state for a project."""
    state = _get_or_create(db, project_id)
    return state


@router.put(
    "/projects/{project_id}/workspace",
    response_model=WorkspaceStateResponse,
)
async def update_workspace_state(
    project_id: str,
    data: WorkspaceStateUpdate,
    db: Session = Depends(get_db),
) -> WorkspaceStateResponse:
    """Update workspace state (partial update)."""
    state = _get_or_create(db, project_id)

    updates = data.model_dump(exclude_none=True)
    for key, value in updates.items():
        if hasattr(state, key):
            setattr(state, key, value)

    state.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(state)
    return state
