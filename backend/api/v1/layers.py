"""Layer API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from geo.layer_service import LayerService

router = APIRouter(prefix="/projects/{project_id}/layers", tags=["Layers"])


# ============================================================
# Pydantic Schemas
# ============================================================


class LayerCreate(BaseModel):
    """Schema for creating a layer."""

    name: str = Field(..., min_length=1, max_length=255, description="Layer name")
    layer_type: str = Field(
        ..., description="Layer type (aoi, vector, raster, drawing, temporary, satellite, ai)"
    )
    source_id: str | None = Field(None, description="Source ID (AOI ID, etc.)")
    source_type: str | None = Field(None, description="Source type")
    style: dict | None = Field(None, description="Style properties")
    extra_metadata: dict | None = Field(None, description="Metadata")
    z_index: int = Field(0, description="Z-index for ordering")


class LayerUpdate(BaseModel):
    """Schema for updating a layer."""

    name: str | None = Field(None, min_length=1, max_length=255)
    visible: bool | None = None
    opacity: float | None = Field(None, ge=0, le=1)
    z_index: int | None = None
    style: dict | None = None
    extra_metadata: dict | None = None


class LayerResponse(BaseModel):
    """Schema for layer response."""

    id: str
    project_id: str
    name: str
    layer_type: str
    visible: bool
    opacity: float
    z_index: int
    source_id: str | None
    source_type: str | None
    style: str | None
    extra_metadata: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReorderRequest(BaseModel):
    """Schema for reordering layers."""

    layer_ids: list[str] = Field(..., description="Ordered list of layer IDs")


# ============================================================
# Endpoints
# ============================================================


@router.post("", response_model=LayerResponse, status_code=201)
async def create_layer(
    project_id: str,
    data: LayerCreate,
    db: Session = Depends(get_db),
) -> LayerResponse:
    """Create a new layer."""
    service = LayerService(db)
    try:
        layer = service.create_layer(
            project_id=project_id,
            name=data.name,
            layer_type=data.layer_type,
            source_id=data.source_id,
            source_type=data.source_type,
            style=data.style,
            extra_metadata=data.extra_metadata,
            z_index=data.z_index,
        )
        return layer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[LayerResponse])
async def list_layers(
    project_id: str,
    db: Session = Depends(get_db),
) -> list[LayerResponse]:
    """List all layers for a project."""
    service = LayerService(db)
    return service.get_project_layers(project_id)


@router.get("/{layer_id}", response_model=LayerResponse)
async def get_layer(
    project_id: str,
    layer_id: str,
    db: Session = Depends(get_db),
) -> LayerResponse:
    """Get a layer by ID."""
    service = LayerService(db)
    layer = service.get_layer(layer_id)
    if not layer or layer.project_id != project_id:
        raise HTTPException(status_code=404, detail="Layer not found")
    return layer


@router.put("/{layer_id}", response_model=LayerResponse)
async def update_layer(
    project_id: str,
    layer_id: str,
    data: LayerUpdate,
    db: Session = Depends(get_db),
) -> LayerResponse:
    """Update a layer."""
    service = LayerService(db)
    try:
        updates = data.model_dump(exclude_none=True)
        layer = service.update_layer(layer_id, **updates)
        if not layer or layer.project_id != project_id:
            raise HTTPException(status_code=404, detail="Layer not found")
        return layer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{layer_id}/toggle-visibility", response_model=LayerResponse)
async def toggle_visibility(
    project_id: str,
    layer_id: str,
    db: Session = Depends(get_db),
) -> LayerResponse:
    """Toggle layer visibility."""
    service = LayerService(db)
    try:
        layer = service.toggle_visibility(layer_id)
        if layer.project_id != project_id:
            raise HTTPException(status_code=404, detail="Layer not found")
        return layer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{layer_id}", status_code=204)
async def delete_layer(
    project_id: str,
    layer_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Delete a layer."""
    service = LayerService(db)
    try:
        layer = service.get_layer(layer_id)
        if not layer or layer.project_id != project_id:
            raise HTTPException(status_code=404, detail="Layer not found")
        service.delete_layer(layer_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reorder", response_model=list[LayerResponse])
async def reorder_layers(
    project_id: str,
    data: ReorderRequest,
    db: Session = Depends(get_db),
) -> list[LayerResponse]:
    """Reorder layers."""
    service = LayerService(db)
    return service.reorder_layers(project_id, data.layer_ids)
