"""AOI API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from geo.aoi_service import AOIService

router = APIRouter(prefix="/projects/{project_id}/aoi", tags=["AOI"])


# ============================================================
# Pydantic Schemas
# ============================================================


class AOICreate(BaseModel):
    """Schema for creating an AOI."""

    name: str = Field(..., min_length=1, max_length=255, description="AOI name")
    description: str | None = Field(None, description="AOI description")
    geometry: dict = Field(..., description="GeoJSON geometry")
    fill_color: str = Field("#3388ff", description="Fill color hex")
    fill_opacity: float = Field(0.2, ge=0, le=1, description="Fill opacity")
    stroke_color: str = Field("#3388ff", description="Stroke color hex")
    stroke_width: float = Field(2.0, ge=0, description="Stroke width")


class AOIUpdate(BaseModel):
    """Schema for updating an AOI."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    geometry: dict | None = None
    fill_color: str | None = None
    fill_opacity: float | None = Field(None, ge=0, le=1)
    stroke_color: str | None = None
    stroke_width: float | None = Field(None, ge=0)


class AOIResponse(BaseModel):
    """Schema for AOI response."""

    id: str
    project_id: str
    name: str
    description: str | None
    geometry: str
    geometry_type: str
    bbox: str | None
    area_m2: float | None
    fill_color: str
    fill_opacity: float
    stroke_color: str
    stroke_width: float
    source: str
    source_file: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Endpoints
# ============================================================


@router.post("", response_model=AOIResponse, status_code=201)
async def create_aoi(
    project_id: str,
    data: AOICreate,
    db: Session = Depends(get_db),
) -> AOIResponse:
    """Create a new AOI."""
    service = AOIService(db)
    try:
        aoi = service.create_aoi(
            project_id=project_id,
            name=data.name,
            geometry=data.geometry,
            description=data.description,
            fill_color=data.fill_color,
            fill_opacity=data.fill_opacity,
            stroke_color=data.stroke_color,
            stroke_width=data.stroke_width,
        )
        return aoi
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[AOIResponse])
async def list_aois(
    project_id: str,
    db: Session = Depends(get_db),
) -> list[AOIResponse]:
    """List all AOIs for a project."""
    service = AOIService(db)
    return service.get_project_aois(project_id)


@router.get("/{aoi_id}", response_model=AOIResponse)
async def get_aoi(
    project_id: str,
    aoi_id: str,
    db: Session = Depends(get_db),
) -> AOIResponse:
    """Get an AOI by ID."""
    service = AOIService(db)
    aoi = service.get_aoi(aoi_id)
    if not aoi or aoi.project_id != project_id:
        raise HTTPException(status_code=404, detail="AOI not found")
    return aoi


@router.put("/{aoi_id}", response_model=AOIResponse)
async def update_aoi(
    project_id: str,
    aoi_id: str,
    data: AOIUpdate,
    db: Session = Depends(get_db),
) -> AOIResponse:
    """Update an AOI."""
    service = AOIService(db)
    try:
        updates = data.model_dump(exclude_none=True)
        aoi = service.update_aoi(aoi_id, **updates)
        if not aoi or aoi.project_id != project_id:
            raise HTTPException(status_code=404, detail="AOI not found")
        return aoi
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{aoi_id}", status_code=204)
async def delete_aoi(
    project_id: str,
    aoi_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Delete an AOI."""
    service = AOIService(db)
    try:
        aoi = service.get_aoi(aoi_id)
        if not aoi or aoi.project_id != project_id:
            raise HTTPException(status_code=404, detail="AOI not found")
        service.delete_aoi(aoi_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
