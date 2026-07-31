"""Raster Processing Engine API endpoints."""

import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.settings import settings
from database.connection import get_db
from raster_engine.database.models import (
    RasterDerivedProduct,
    RasterMetadata,
    RasterProcessingHistory,
)
from raster_engine.services import (
    build_overviews,
    calculate_histogram,
    calculate_statistics,
    clip_raster_with_polygon,
    crop_raster,
    extract_bands,
    fill_nodata,
    generate_thumbnail,
    mosaic_rasters,
    read_metadata,
    reproject_raster,
    resample_raster,
    save_metadata_to_db,
    set_nodata,
)
from raster_engine.services.import_service import import_raster_upload
from raster_engine.services.tile_server import serve_tile, tile_cache_path

router = APIRouter(prefix="/rasters", tags=["Raster Processing"])


# ============================================================
# Pydantic Schemas
# ============================================================


class RasterMetadataResponse(BaseModel):
    """Schema for raster metadata response."""

    id: str
    dataset_id: str | None = None
    project_id: str
    file_path: str
    width: int
    height: int
    band_count: int
    data_type: str
    nodata_value: float | None = None
    crs: str
    resolution_x: float
    resolution_y: float
    bounds_min_x: float
    bounds_min_y: float
    bounds_max_x: float
    bounds_max_y: float
    file_format: str
    file_size: int
    has_overviews: bool
    compression: str | None = None
    statistics: str | None = None
    histogram: str | None = None
    created_at: datetime
    updated_at: datetime


class ReprojectRequest(BaseModel):
    """Schema for reprojection request."""

    target_crs: str = Field(..., description="Target CRS (e.g., EPSG:32633)")
    resampling: str = Field("nearest", description="Resampling method")


class CropRequest(BaseModel):
    """Schema for crop request."""

    bbox: tuple[float, float, float, float] = Field(
        ..., description="(min_x, min_y, max_x, max_y)"
    )


class ClipRequest(BaseModel):
    """Schema for clip request."""

    geometry: dict = Field(..., description="GeoJSON geometry")
    all_touched: bool = Field(True, description="Include all touched pixels")


class ResampleRequest(BaseModel):
    """Schema for resample request."""

    target_width: int | None = Field(None, description="Target width in pixels")
    target_height: int | None = Field(None, description="Target height in pixels")
    target_resolution: tuple[float, float] | None = Field(
        None, description="(x, y) target resolution"
    )
    resampling: str = Field("nearest", description="Resampling method")


class BandsRequest(BaseModel):
    """Schema for band extraction request."""

    bands: list[int] = Field(..., description="Band numbers to extract (1-based)")


class NodataRequest(BaseModel):
    """Schema for nodata operation request."""

    operation: str = Field(..., description="'set' or 'fill'")
    nodata_value: float | None = Field(None, description="Value to set as nodata")
    fill_value: float | None = Field(None, description="Constant fill value")
    use_interpolation: bool = Field(True, description="Use interpolation for fill")


class OverviewRequest(BaseModel):
    """Schema for overview generation request."""

    levels: list[int] | None = Field(None, description="Overview levels")
    resampling: str = Field("nearest", description="Resampling method")


class MosaicRequest(BaseModel):
    """Schema for mosaic request."""

    file_paths: list[str] = Field(..., description="Input file paths")
    output_filename: str = Field("mosaic.tif", description="Output filename")
    method: str = Field("first", description="Merge method")


class RasterImportResponse(BaseModel):
    """Schema for raster import response."""

    layer_id: str
    raster_id: str
    project_id: str
    name: str
    file_path: str
    crs: str | None
    width: int
    height: int
    band_count: int
    file_size: int
    tile_url_template: str


# ============================================================
# Endpoints — fixed paths BEFORE wildcards
# ============================================================


@router.post("/{project_id}/metadata", response_model=RasterMetadataResponse)
async def extract_metadata(
    project_id: str,
    file_path: str,
    dataset_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Extract and store raster metadata."""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    metadata = read_metadata(file_path)
    raster_id = save_metadata_to_db(db, project_id, dataset_id, file_path, metadata)

    raster = db.query(RasterMetadata).filter(RasterMetadata.id == raster_id).first()
    return raster


@router.get("/{project_id}/list", response_model=list[RasterMetadataResponse])
async def list_rasters(
    project_id: str,
    db: Session = Depends(get_db),
):
    """List all raster metadata for a project."""
    rasters = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.project_id == project_id)
        .all()
    )
    return rasters


@router.get("/{project_id}/history", response_model=list)
async def get_processing_history(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Get raster processing history for a project."""
    history = (
        db.query(RasterProcessingHistory)
        .filter(RasterProcessingHistory.project_id == project_id)
        .order_by(RasterProcessingHistory.created_at.desc())
        .all()
    )
    return [
        {
            "id": h.id,
            "operation": h.operation,
            "status": h.status,
            "input_path": h.input_path,
            "output_path": h.output_path,
            "error_message": h.error_message,
            "execution_time_ms": h.execution_time_ms,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]


@router.get("/{project_id}/derived", response_model=list)
async def get_derived_products(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Get derived products for a project."""
    products = (
        db.query(RasterDerivedProduct)
        .filter(RasterDerivedProduct.project_id == project_id)
        .order_by(RasterDerivedProduct.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "source_dataset_id": p.source_dataset_id,
            "operation": p.operation,
            "output_path": p.output_path,
            "output_filename": p.output_filename,
            "file_size": p.file_size,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ]


@router.post("/{project_id}/mosaic")
async def mosaic(
    project_id: str,
    request: MosaicRequest,
    db: Session = Depends(get_db),
):
    """Mosaic multiple rasters."""
    for fp in request.file_paths:
        if not os.path.exists(fp):
            raise HTTPException(status_code=404, detail=f"File not found: {fp}")

    output_path = str(Path(request.file_paths[0]).parent / request.output_filename)
    result = mosaic_rasters(request.file_paths, output_path, request.method)

    history = RasterProcessingHistory(
        id=str(uuid.uuid4()),
        dataset_id=None,
        project_id=project_id,
        operation="mosaic",
        parameters=request.model_dump_json(),
        status="completed",
        input_path=",".join(request.file_paths),
        output_path=output_path,
    )
    db.add(history)
    db.commit()

    return result


# ============================================================
# Endpoints — wildcard {raster_id} routes below
# ============================================================


@router.get("/{project_id}/{raster_id}", response_model=RasterMetadataResponse)
async def get_raster(
    project_id: str,
    raster_id: str,
    db: Session = Depends(get_db),
):
    """Get raster metadata by ID."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")
    return raster


@router.get("/{project_id}/{raster_id}/statistics")
async def get_statistics(
    project_id: str,
    raster_id: str,
    db: Session = Depends(get_db),
):
    """Calculate and return raster statistics."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    stats = calculate_statistics(raster.file_path if hasattr(raster, 'file_path') else "")
    return stats


@router.get("/{project_id}/{raster_id}/histogram")
async def get_histogram(
    project_id: str,
    raster_id: str,
    bins: int = 256,
    db: Session = Depends(get_db),
):
    """Calculate and return raster histogram."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    hist = calculate_histogram(raster.file_path if hasattr(raster, 'file_path') else "", bins=bins)
    return hist


@router.post("/{project_id}/{raster_id}/reproject")
async def reproject(
    project_id: str,
    raster_id: str,
    request: ReprojectRequest,
    db: Session = Depends(get_db),
):
    """Reproject a raster to a target CRS."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    output_path = str(Path(raster.file_path).parent / f"{Path(raster.file_path).stem}_reproj.tif")
    result = reproject_raster(raster.file_path, output_path, request.target_crs, request.resampling)

    history = RasterProcessingHistory(
        id=str(uuid.uuid4()),
        dataset_id=raster.dataset_id,
        project_id=project_id,
        operation="reproject",
        parameters=request.model_dump_json(),
        status="completed",
        input_path=raster.file_path,
        output_path=output_path,
    )
    db.add(history)
    db.commit()

    return result


@router.post("/{project_id}/{raster_id}/crop")
async def crop(
    project_id: str,
    raster_id: str,
    request: CropRequest,
    db: Session = Depends(get_db),
):
    """Crop a raster to a bounding box."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    output_path = str(Path(raster.file_path).parent / f"{Path(raster.file_path).stem}_cropped.tif")
    result = crop_raster(raster.file_path, output_path, request.bbox)

    history = RasterProcessingHistory(
        id=str(uuid.uuid4()),
        dataset_id=raster.dataset_id,
        project_id=project_id,
        operation="crop",
        parameters=request.model_dump_json(),
        status="completed",
        input_path=raster.file_path,
        output_path=output_path,
    )
    db.add(history)
    db.commit()

    return result


@router.post("/{project_id}/{raster_id}/clip")
async def clip(
    project_id: str,
    raster_id: str,
    request: ClipRequest,
    db: Session = Depends(get_db),
):
    """Clip a raster with a polygon geometry."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    output_path = str(Path(raster.file_path).parent / f"{Path(raster.file_path).stem}_clipped.tif")
    result = clip_raster_with_polygon(raster.file_path, output_path, request.geometry, request.all_touched)

    history = RasterProcessingHistory(
        id=str(uuid.uuid4()),
        dataset_id=raster.dataset_id,
        project_id=project_id,
        operation="clip",
        parameters=request.model_dump_json(),
        status="completed",
        input_path=raster.file_path,
        output_path=output_path,
    )
    db.add(history)
    db.commit()

    return result


@router.post("/{project_id}/{raster_id}/resample")
async def resample(
    project_id: str,
    raster_id: str,
    request: ResampleRequest,
    db: Session = Depends(get_db),
):
    """Resample a raster to a new resolution."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    output_path = str(Path(raster.file_path).parent / f"{Path(raster.file_path).stem}_resampled.tif")
    result = resample_raster(
        raster.file_path, output_path,
        request.target_width, request.target_height,
        request.target_resolution, request.resampling,
    )

    history = RasterProcessingHistory(
        id=str(uuid.uuid4()),
        dataset_id=raster.dataset_id,
        project_id=project_id,
        operation="resample",
        parameters=request.model_dump_json(),
        status="completed",
        input_path=raster.file_path,
        output_path=output_path,
    )
    db.add(history)
    db.commit()

    return result


@router.post("/{project_id}/{raster_id}/overview")
async def create_overview(
    project_id: str,
    raster_id: str,
    request: OverviewRequest,
    db: Session = Depends(get_db),
):
    """Build overview pyramids for a raster."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    output_path = str(Path(raster.file_path).parent / f"{Path(raster.file_path).stem}_pyramid.tif")
    result = build_overviews(raster.file_path, output_path, request.levels, request.resampling)

    raster.has_overviews = True
    db.commit()

    return result


@router.post("/{project_id}/{raster_id}/bands")
async def extract_bands_from_raster(
    project_id: str,
    raster_id: str,
    request: BandsRequest,
    db: Session = Depends(get_db),
):
    """Extract specific bands from a raster."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    output_path = str(Path(raster.file_path).parent / f"{Path(raster.file_path).stem}_bands.tif")
    result = extract_bands(raster.file_path, output_path, request.bands)

    history = RasterProcessingHistory(
        id=str(uuid.uuid4()),
        dataset_id=raster.dataset_id,
        project_id=project_id,
        operation="extract_bands",
        parameters=request.model_dump_json(),
        status="completed",
        input_path=raster.file_path,
        output_path=output_path,
    )
    db.add(history)
    db.commit()

    return result


@router.post("/{project_id}/{raster_id}/nodata")
async def handle_nodata(
    project_id: str,
    raster_id: str,
    request: NodataRequest,
    db: Session = Depends(get_db),
):
    """Set or fill nodata values."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    output_path = str(Path(raster.file_path).parent / f"{Path(raster.file_path).stem}_nodata.tif")

    if request.operation == "set":
        if request.nodata_value is None:
            raise HTTPException(status_code=400, detail="nodata_value required for set operation")
        result = set_nodata(raster.file_path, output_path, request.nodata_value)
    elif request.operation == "fill":
        result = fill_nodata(raster.file_path, output_path, request.fill_value, request.use_interpolation)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")

    return result


@router.post("/{project_id}/thumbnail")
async def create_thumbnail(
    project_id: str,
    raster_id: str,
    width: int = 256,
    height: int = 256,
    db: Session = Depends(get_db),
):
    """Generate a thumbnail image for a raster."""
    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    output_path = str(Path(raster.file_path).parent / f"{Path(raster.file_path).stem}_thumb.png")
    result = generate_thumbnail(raster.file_path, output_path, width, height)

    return result


# ============================================================
# GIS Workspace endpoints
# ============================================================


@router.post("/{project_id}/import", response_model=RasterImportResponse, status_code=201)
async def import_raster(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> RasterImportResponse:
    """Import an uploaded raster file as a GIS layer (tiles served on demand)."""
    content = await file.read()
    try:
        layer, metadata = import_raster_upload(
            db, project_id, content, file.filename or "raster"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    raster_id = layer.source_id
    return RasterImportResponse(
        layer_id=layer.id,
        raster_id=raster_id or "",
        project_id=project_id,
        name=layer.name,
        file_path=metadata.get("file_path") or "",
        crs=metadata.get("crs"),
        width=int(metadata.get("width") or 0),
        height=int(metadata.get("height") or 0),
        band_count=int(metadata.get("band_count") or 0),
        file_size=int(metadata.get("file_size") or 0),
        tile_url_template=f"/api/v1/rasters/{project_id}/{raster_id}/tiles/{{z}}/{{x}}/{{y}}.png",
    )


@router.get("/{project_id}/{raster_id}/tiles/{z}/{x}/{y}.png")
async def get_raster_tile(
    project_id: str,
    raster_id: str,
    z: int,
    x: int,
    y: int,
    db: Session = Depends(get_db),
) -> Response:
    """Serve a web-mercator PNG tile for a raster (backed by on-disk cache)."""
    if not (0 <= z <= 24) or x < 0 or y < 0 or x > 2 ** z - 1 or y > 2 ** z - 1:
        raise HTTPException(status_code=400, detail="Invalid tile coordinates")

    raster = (
        db.query(RasterMetadata)
        .filter(RasterMetadata.id == raster_id, RasterMetadata.project_id == project_id)
        .first()
    )
    if not raster:
        raise HTTPException(status_code=404, detail="Raster not found")

    cache_path = tile_cache_path(settings.CACHE_DIR, raster.id, z, x, y)
    if cache_path.exists():
        return Response(
            content=cache_path.read_bytes(),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    png = serve_tile(raster.file_path, z, x, y)
    if png is None:
        raise HTTPException(status_code=404, detail="No data for tile")

    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(png)
    except OSError:
        pass

    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
