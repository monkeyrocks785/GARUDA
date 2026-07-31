"""GIS Workspace API endpoints - offline basemaps and workspace support."""

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from gis_engine.basemap_service import (
    delete_basemap,
    list_basemaps,
    register_geotiff_basemap,
    serve_registered_tile,
    serve_xyz_tile,
)

router = APIRouter(prefix="/gis", tags=["GIS Workspace"])


class BasemapResponse(BaseModel):
    """Schema for a basemap entry."""

    id: str
    name: str
    basemap_type: str
    crs: str | None
    tile_url_template: str


class GeoTiffRegisterRequest(BaseModel):
    """Schema for registering a GeoTIFF basemap."""

    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(..., description="Absolute path inside configured storage")


@router.get("/basemaps", response_model=list[BasemapResponse])
async def get_basemaps(db: Session = Depends(get_db)) -> list[BasemapResponse]:
    """List all available offline basemaps (blank grid + local sources)."""
    return [BasemapResponse(**b) for b in list_basemaps(db)]


@router.post("/basemaps/geotiff", response_model=BasemapResponse, status_code=201)
async def register_geotiff(
    request: GeoTiffRegisterRequest,
    db: Session = Depends(get_db),
) -> BasemapResponse:
    """Register a local raster file as an offline basemap."""
    try:
        basemap = register_geotiff_basemap(db, request.name, request.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return BasemapResponse(
        id=basemap.id,
        name=basemap.name,
        basemap_type=basemap.basemap_type,
        crs=basemap.crs,
        tile_url_template=f"/api/v1/gis/basemaps/{basemap.id}/tiles/{{z}}/{{x}}/{{y}}.png",
    )


@router.delete("/basemaps/{basemap_id}", status_code=204)
async def remove_basemap(
    basemap_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Unregister a basemap."""
    if not delete_basemap(db, basemap_id):
        raise HTTPException(status_code=404, detail="Basemap not found")


@router.get("/basemaps/{basemap_id}/tiles/{z}/{x}/{y}.png")
async def get_basemap_tile(
    basemap_id: str,
    z: int,
    x: int,
    y: int,
    db: Session = Depends(get_db),
) -> Response:
    """Serve an offline basemap tile (local XYZ folder or GeoTIFF)."""
    if not (0 <= z <= 24) or x < 0 or y < 0 or x > 2 ** z - 1 or y > 2 ** z - 1:
        raise HTTPException(status_code=400, detail="Invalid tile coordinates")

    if basemap_id.startswith("xyz-"):
        png = serve_xyz_tile(basemap_id, z, x, y)
    else:
        png = serve_registered_tile(db, basemap_id, z, x, y)

    if png is None:
        raise HTTPException(status_code=404, detail="No data for tile")
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
