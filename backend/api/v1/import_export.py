"""File import/export API endpoints."""

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from geo.file_export_service import FileExportService
from geo.file_import_service import FileImportService

router = APIRouter(tags=["Import/Export"])


# ============================================================
# Pydantic Schemas
# ============================================================


class ImportResponse(BaseModel):
    """Schema for import response."""

    file_id: str
    layer_id: str
    filename: str
    file_type: str
    feature_count: int
    geometry_type: str | None


class ExportRequest(BaseModel):
    """Schema for export request."""

    aoi_ids: list[str] = []
    geometry_ids: list[str] = []
    name: str | None = None


class ExportResponse(BaseModel):
    """Schema for export response."""

    content: str
    filename: str
    format: str


# ============================================================
# Import Endpoints
# ============================================================


@router.post(
    "/projects/{project_id}/import/geojson",
    response_model=ImportResponse,
    status_code=201,
)
async def import_geojson(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImportResponse:
    """Import a GeoJSON file."""
    if not file.filename.endswith(".geojson") and not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="File must be .geojson or .json")

    try:
        content = await file.read()
        file_content = content.decode("utf-8")

        service = FileImportService(db)
        imported_file, layer = service.import_geojson(
            project_id=project_id,
            file_content=file_content,
            filename=file.filename,
        )

        return ImportResponse(
            file_id=imported_file.id,
            layer_id=layer.id,
            filename=imported_file.original_filename,
            file_type="geojson",
            feature_count=imported_file.feature_count,
            geometry_type=imported_file.geometry_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/projects/{project_id}/import/kml",
    response_model=ImportResponse,
    status_code=201,
)
async def import_kml(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImportResponse:
    """Import a KML file."""
    if not file.filename.endswith(".kml"):
        raise HTTPException(status_code=400, detail="File must be .kml")

    try:
        content = await file.read()
        file_content = content.decode("utf-8")

        service = FileImportService(db)
        imported_file, layer = service.import_kml(
            project_id=project_id,
            file_content=file_content,
            filename=file.filename,
        )

        return ImportResponse(
            file_id=imported_file.id,
            layer_id=layer.id,
            filename=imported_file.original_filename,
            file_type="kml",
            feature_count=imported_file.feature_count,
            geometry_type=imported_file.geometry_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/projects/{project_id}/import/shapefile",
    response_model=ImportResponse,
    status_code=201,
)
async def import_shapefile(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImportResponse:
    """Import a Shapefile (ZIP containing .shp, .dbf, .shx, .prj)."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be .zip")

    try:
        content = await file.read()

        service = FileImportService(db)
        imported_file, layer = service.import_shapefile(
            project_id=project_id,
            zip_content=content,
            filename=file.filename,
        )

        return ImportResponse(
            file_id=imported_file.id,
            layer_id=layer.id,
            filename=imported_file.original_filename,
            file_type="shapefile",
            feature_count=imported_file.feature_count,
            geometry_type=imported_file.geometry_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Export Endpoints
# ============================================================


@router.post(
    "/projects/{project_id}/export/geojson",
    response_model=ExportResponse,
)
async def export_geojson(
    project_id: str,
    data: ExportRequest,
    db: Session = Depends(get_db),
) -> ExportResponse:
    """Export AOIs to GeoJSON."""
    from models.aoi import AOI

    service = FileExportService()

    # Get AOIs
    geometries = []
    names = []
    for aoi_id in data.aoi_ids:
        aoi = db.query(AOI).filter(AOI.id == aoi_id, AOI.project_id == project_id).first()
        if aoi:
            geometries.append(json.loads(aoi.geometry))
            names.append(aoi.name)

    if not geometries:
        raise HTTPException(status_code=400, detail="No valid geometries to export")

    content = service.export_geojson(geometries, names)
    filename = f"{data.name or 'garuda_export'}.geojson"

    return ExportResponse(content=content, filename=filename, format="geojson")


@router.post(
    "/projects/{project_id}/export/kml",
    response_model=ExportResponse,
)
async def export_kml(
    project_id: str,
    data: ExportRequest,
    db: Session = Depends(get_db),
) -> ExportResponse:
    """Export AOIs to KML."""
    from models.aoi import AOI

    service = FileExportService()

    # Get AOIs
    geometries = []
    names = []
    for aoi_id in data.aoi_ids:
        aoi = db.query(AOI).filter(AOI.id == aoi_id, AOI.project_id == project_id).first()
        if aoi:
            geometries.append(json.loads(aoi.geometry))
            names.append(aoi.name)

    if not geometries:
        raise HTTPException(status_code=400, detail="No valid geometries to export")

    content = service.export_kml(geometries, names, document_name=data.name or "GARUDA Export")
    filename = f"{data.name or 'garuda_export'}.kml"

    return ExportResponse(content=content, filename=filename, format="kml")
