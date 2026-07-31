"""Dataset API endpoints for GARUDA Data Engine."""

import os
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.settings import settings
from data_engine.catalog import get_dataset, search_datasets
from data_engine.services import DatasetService
from database.connection import get_db

router = APIRouter(prefix="/datasets", tags=["Datasets"])


# ============================================================
# Pydantic Schemas
# ============================================================


class DatasetResponse(BaseModel):
    """Schema for dataset response."""

    id: str
    project_id: str
    name: str
    description: str | None
    dataset_type: str
    original_filename: str
    extension: str
    coordinate_system: str | None
    bbox_min_x: float | None
    bbox_min_y: float | None
    bbox_max_x: float | None
    bbox_max_y: float | None
    resolution_x: float | None
    resolution_y: float | None
    bands: int | None
    width: int | None
    height: int | None
    file_size: int
    checksum: str
    status: str
    version: int
    is_favorite: bool
    is_archived: bool
    source: str | None
    storage_path: str
    tags: str | None
    notes: str | None
    created_at: datetime
    modified_at: datetime
    imported_at: datetime

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Schema for dataset list response."""

    datasets: list[DatasetResponse]
    total: int
    offset: int
    limit: int


class DatasetUpdate(BaseModel):
    """Schema for updating dataset."""

    name: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    notes: str | None = None


class TagRequest(BaseModel):
    """Schema for tag operations."""

    tag: str = Field(..., min_length=1, max_length=100)


class ImportResponse(BaseModel):
    """Schema for import response."""

    success: bool
    dataset_id: str | None
    version: int
    is_duplicate: bool
    is_new_version: bool
    errors: list[str]
    warnings: list[str]


class ImportMultipleResponse(BaseModel):
    """Schema for multiple import response."""

    results: list[ImportResponse]
    total: int
    imported: int
    duplicates: int
    errors: int


class SearchRequest(BaseModel):
    """Schema for search request."""

    query: str | None = None
    dataset_type: str | None = None
    extension: str | None = None
    tags: list[str] | None = None
    favorite_only: bool = False
    sort_by: str = "created_at"
    sort_order: str = "desc"


class DatasetStatsResponse(BaseModel):
    """Schema for dataset statistics."""

    total: int
    by_type: dict
    by_extension: dict
    total_size_bytes: int


class VersionResponse(BaseModel):
    """Schema for version history."""

    id: str
    version_number: int
    checksum: str
    file_size: int
    change_description: str
    created_at: str | None


# ============================================================
# API Endpoints
# ============================================================


@router.post("/import", response_model=ImportResponse, status_code=201)
async def import_dataset(
    project_id: str = Query(..., description="Project ID"),
    name: str | None = Query(None, description="Dataset name"),
    description: str | None = Query(None, description="Dataset description"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import a single file as a dataset."""
    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        service = DatasetService(db, Path(settings.STORAGE_DIR))
        tag_list = tags.split(",") if tags else None

        result = service.import_file(
            file_path=tmp_path,
            project_id=project_id,
            name=name,
            description=description,
            tags=tag_list,
            imported_by="api",
        )

        return ImportResponse(**result.to_dict())
    finally:
        os.unlink(tmp_path)


@router.post("/import-folder", response_model=ImportMultipleResponse)
async def import_folder_endpoint(
    project_id: str = Query(..., description="Project ID"),
    folder_path: str = Query(..., description="Folder path to import"),
    recursive: bool = Query(True, description="Scan recursively"),
    db: Session = Depends(get_db),
):
    """Import all supported files from a folder."""
    folder = Path(folder_path)
    if not folder.exists():
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path}")

    service = DatasetService(db, Path(settings.STORAGE_DIR))
    results = service.import_folder(
        folder_path=folder,
        project_id=project_id,
        recursive=recursive,
        imported_by="api",
    )

    imported = sum(1 for r in results if r.success and not r.is_duplicate)
    duplicates = sum(1 for r in results if r.is_duplicate)
    errors = sum(1 for r in results if not r.success)

    return ImportMultipleResponse(
        results=[ImportResponse(**r.to_dict()) for r in results],
        total=len(results),
        imported=imported,
        duplicates=duplicates,
        errors=errors,
    )


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    project_id: str = Query(..., description="Project ID"),
    query: str | None = Query(None, description="Search query"),
    dataset_type: str | None = Query(None, description="Dataset type"),
    extension: str | None = Query(None, description="File extension"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    favorite_only: bool = Query(False, description="Favorites only"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List datasets with search and filters."""
    tag_list = tags.split(",") if tags else None

    datasets, total = search_datasets(
        db=db,
        project_id=project_id,
        query=query,
        dataset_type=dataset_type,
        extension=extension,
        tags=tag_list,
        favorite_only=favorite_only,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
    )

    return DatasetListResponse(
        datasets=[DatasetResponse.model_validate(d) for d in datasets],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/search", response_model=DatasetListResponse)
async def search_datasets_endpoint(
    project_id: str = Query(..., description="Project ID"),
    q: str | None = Query(None, alias="q", description="Search query"),
    dataset_type: str | None = Query(None, description="Dataset type"),
    extension: str | None = Query(None, description="File extension"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    favorite_only: bool = Query(False, description="Favorites only"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Search datasets."""
    tag_list = tags.split(",") if tags else None

    datasets, total = search_datasets(
        db=db,
        project_id=project_id,
        query=q,
        dataset_type=dataset_type,
        extension=extension,
        tags=tag_list,
        favorite_only=favorite_only,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
    )

    return DatasetListResponse(
        datasets=[DatasetResponse.model_validate(d) for d in datasets],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset_endpoint(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """Get a single dataset by ID."""
    dataset = get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetResponse.model_validate(dataset)


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset_endpoint(
    dataset_id: str,
    update: DatasetUpdate,
    db: Session = Depends(get_db),
):
    """Update dataset metadata."""
    service = DatasetService(db, Path(settings.STORAGE_DIR))
    dataset = service.update(
        dataset_id=dataset_id,
        name=update.name,
        description=update.description,
        notes=update.notes,
    )
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetResponse.model_validate(dataset)


@router.delete("/{dataset_id}")
async def delete_dataset_endpoint(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """Delete a dataset."""
    service = DatasetService(db, Path(settings.STORAGE_DIR))
    success = service.delete(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"success": True, "message": "Dataset deleted"}


@router.post("/{dataset_id}/favorite")
async def toggle_favorite_endpoint(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """Toggle favorite status."""
    service = DatasetService(db, Path(settings.STORAGE_DIR))
    is_favorite = service.toggle_favorite(dataset_id)
    return {"is_favorite": is_favorite}


@router.post("/{dataset_id}/tag")
async def add_tag_endpoint(
    dataset_id: str,
    request: TagRequest,
    db: Session = Depends(get_db),
):
    """Add a tag to a dataset."""
    service = DatasetService(db, Path(settings.STORAGE_DIR))
    success = service.add_tag(dataset_id, request.tag)
    if not success:
        raise HTTPException(status_code=400, detail="Tag already exists")
    return {"success": True}


@router.delete("/{dataset_id}/tag/{tag}")
async def remove_tag_endpoint(
    dataset_id: str,
    tag: str,
    db: Session = Depends(get_db),
):
    """Remove a tag from a dataset."""
    service = DatasetService(db, Path(settings.STORAGE_DIR))
    success = service.remove_tag(dataset_id, tag)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"success": True}


@router.get("/{dataset_id}/versions", response_model=list[VersionResponse])
async def get_versions_endpoint(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """Get version history for a dataset."""
    service = DatasetService(db, Path(settings.STORAGE_DIR))
    versions = service.get_version_history(dataset_id)
    return [VersionResponse(**v) for v in versions]


@router.get("/{dataset_id}/metadata")
async def get_metadata_endpoint(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """Get metadata for a dataset."""
    service = DatasetService(db, Path(settings.STORAGE_DIR))
    metadata = service.get_metadata(dataset_id)
    return metadata


@router.get("/stats/{project_id}", response_model=DatasetStatsResponse)
async def get_stats_endpoint(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Get dataset statistics for a project."""
    service = DatasetService(db, Path(settings.STORAGE_DIR))
    stats = service.get_stats(project_id)
    return DatasetStatsResponse(**stats)
