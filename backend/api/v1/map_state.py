"""Map state API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from geo.map_state_service import MapStateService

router = APIRouter(prefix="/projects/{project_id}/map-state", tags=["Map State"])


# ============================================================
# Pydantic Schemas
# ============================================================


class MapStateResponse(BaseModel):
    """Schema for map state response."""

    project_id: str
    zoom: float
    center_lat: float
    center_lng: float
    map_rotation: float
    basemap: str
    visible_layers: str | None
    selected_layer_id: str | None
    sidebar_width: int
    panel_visible: bool
    active_tool: str | None
    updated_at: datetime

    class Config:
        from_attributes = True


class MapStateUpdate(BaseModel):
    """Schema for updating map state."""

    zoom: float | None = Field(None, ge=0, le=20)
    center_lat: float | None = Field(None, ge=-90, le=90)
    center_lng: float | None = Field(None, ge=-180, le=180)
    map_rotation: float | None = None
    basemap: str | None = None
    visible_layers: list[str] | None = None
    selected_layer_id: str | None = None
    sidebar_width: int | None = Field(None, ge=200, le=600)
    panel_visible: bool | None = None
    active_tool: str | None = None


# ============================================================
# Endpoints
# ============================================================


@router.get("", response_model=MapStateResponse)
async def get_map_state(
    project_id: str,
    db: Session = Depends(get_db),
) -> MapStateResponse:
    """Get map state for a project."""
    service = MapStateService(db)
    return service.get_map_state(project_id)


@router.put("", response_model=MapStateResponse)
async def update_map_state(
    project_id: str,
    data: MapStateUpdate,
    db: Session = Depends(get_db),
) -> MapStateResponse:
    """Update map state."""
    service = MapStateService(db)
    updates = data.model_dump(exclude_none=True)
    return service.update_map_state(project_id, **updates)
