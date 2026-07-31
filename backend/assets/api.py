"""Asset Library API endpoints."""

import os
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from assets.catalog import search_assets
from assets.collections import list_collections
from assets.services import AssetService
from config.settings import settings
from database.connection import get_db

router = APIRouter(prefix="/assets", tags=["Assets"])


# ============================================================
# Pydantic Schemas
# ============================================================


class AssetResponse(BaseModel):
    """Schema for asset response."""

    id: str
    project_id: str | None
    name: str
    display_name: str | None
    description: str | None
    asset_type: str
    category: str | None
    extension: str
    storage_path: str
    preview_path: str | None
    thumbnail_path: str | None
    file_size: int
    checksum: str
    owner: str | None
    status: str
    version: int
    is_favorite: bool
    is_pinned: bool
    is_archived: bool
    is_hidden: bool
    tags: str | None
    created_at: datetime
    modified_at: datetime
    imported_at: datetime | None
    last_opened_at: datetime | None
    last_used_at: datetime | None

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    """Schema for asset list response."""

    assets: list[AssetResponse]
    total: int
    offset: int
    limit: int


class AssetUpdate(BaseModel):
    """Schema for updating asset."""

    name: str | None = Field(None, min_length=1, max_length=500)
    display_name: str | None = Field(None, max_length=500)
    description: str | None = None
    category: str | None = None
    owner: str | None = None


class TagRequest(BaseModel):
    """Schema for tag operations."""

    tag: str = Field(..., min_length=1, max_length=100)


class RelationshipRequest(BaseModel):
    """Schema for relationship operations."""

    target_asset_id: str
    relationship_type: str


class CollectionCreate(BaseModel):
    """Schema for creating collection."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    project_id: str | None = None
    color: str | None = None
    icon: str | None = None


class CollectionResponse(BaseModel):
    """Schema for collection response."""

    id: str
    name: str
    description: str | None
    project_id: str | None
    color: str | None
    icon: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class CollectionListResponse(BaseModel):
    """Schema for collection list response."""

    collections: list[CollectionResponse]
    total: int


class AssetStatsResponse(BaseModel):
    """Schema for asset statistics."""

    total: int
    by_type: dict
    by_category: dict
    total_size_bytes: int


class HistoryResponse(BaseModel):
    """Schema for history response."""

    id: str
    action: str
    details: str | None
    performed_by: str | None
    timestamp: datetime

    class Config:
        from_attributes = True


class ImportResponse(BaseModel):
    """Schema for import response."""

    success: bool
    asset_id: str
    name: str
    asset_type: str
    is_duplicate: bool


# ============================================================
# Asset Endpoints
# ============================================================


@router.post("/import", response_model=ImportResponse, status_code=201)
async def import_asset(
    project_id: str | None = Query(None, description="Project ID"),
    name: str | None = Query(None, description="Asset name"),
    description: str | None = Query(None, description="Asset description"),
    category: str | None = Query(None, description="Asset category"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import a file as an asset."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        service = AssetService(db, Path(settings.STORAGE_DIR))
        tag_list = tags.split(",") if tags else None

        asset = service.create_asset(
            file_path=tmp_path,
            project_id=project_id,
            name=name,
            description=description,
            category=category,
            tags=tag_list,
            owner="api",
        )

        return ImportResponse(
            success=True,
            asset_id=asset.id,
            name=asset.name,
            asset_type=asset.asset_type,
            is_duplicate=False,
        )
    finally:
        os.unlink(tmp_path)


@router.get("", response_model=AssetListResponse)
async def list_assets(
    project_id: str | None = Query(None, description="Project ID"),
    query: str | None = Query(None, description="Search query"),
    asset_type: str | None = Query(None, description="Asset type"),
    category: str | None = Query(None, description="Category"),
    extension: str | None = Query(None, description="Extension"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    owner: str | None = Query(None, description="Owner"),
    favorite_only: bool = Query(False, description="Favorites only"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List assets with search and filters."""
    tag_list = tags.split(",") if tags else None

    assets, total = search_assets(
        db=db,
        project_id=project_id,
        query=query,
        asset_type=asset_type,
        category=category,
        extension=extension,
        tags=tag_list,
        owner=owner,
        favorite_only=favorite_only,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=limit,
    )

    return AssetListResponse(
        assets=[AssetResponse.model_validate(a) for a in assets],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/search", response_model=AssetListResponse)
async def search_assets_endpoint(
    q: str | None = Query(None, alias="q", description="Search query"),
    project_id: str | None = Query(None, description="Project ID"),
    asset_type: str | None = Query(None, description="Asset type"),
    category: str | None = Query(None, description="Category"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Search assets."""
    tag_list = tags.split(",") if tags else None

    assets, total = search_assets(
        db=db,
        project_id=project_id,
        query=q,
        asset_type=asset_type,
        category=category,
        tags=tag_list,
        offset=offset,
        limit=limit,
    )

    return AssetListResponse(
        assets=[AssetResponse.model_validate(a) for a in assets],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """Get a single asset by ID."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    asset = service.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse.model_validate(asset)


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset_endpoint(
    asset_id: str,
    update: AssetUpdate,
    db: Session = Depends(get_db),
):
    """Update asset metadata."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    asset = service.update(
        asset_id=asset_id,
        name=update.name,
        display_name=update.display_name,
        description=update.description,
        category=update.category,
        owner=update.owner,
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse.model_validate(asset)


@router.delete("/{asset_id}")
async def delete_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """Delete an asset."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    success = service.delete(asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"success": True, "message": "Asset deleted"}


@router.post("/{asset_id}/favorite")
async def toggle_favorite_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """Toggle favorite status."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    is_favorite = service.toggle_favorite(asset_id)
    return {"is_favorite": is_favorite}


@router.post("/{asset_id}/pin")
async def toggle_pin_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """Toggle pin status."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    is_pinned = service.toggle_pin(asset_id)
    return {"is_pinned": is_pinned}


@router.post("/{asset_id}/archive")
async def archive_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """Archive an asset."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    success = service.archive(asset_id)
    return {"success": success}


@router.post("/{asset_id}/restore")
async def restore_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """Restore an archived asset."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    success = service.restore(asset_id)
    return {"success": success}


@router.post("/{asset_id}/tag")
async def add_tag_endpoint(
    asset_id: str,
    request: TagRequest,
    db: Session = Depends(get_db),
):
    """Add a tag to an asset."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    success = service.add_tag(asset_id, request.tag)
    if not success:
        raise HTTPException(status_code=400, detail="Tag already exists")
    return {"success": True}


@router.delete("/{asset_id}/tag/{tag}")
async def remove_tag_endpoint(
    asset_id: str,
    tag: str,
    db: Session = Depends(get_db),
):
    """Remove a tag from an asset."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    success = service.remove_tag(asset_id, tag)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"success": True}


@router.post("/{asset_id}/relationship")
async def create_relationship_endpoint(
    asset_id: str,
    request: RelationshipRequest,
    db: Session = Depends(get_db),
):
    """Create a relationship between assets."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    success = service.create_relationship(
        asset_id, request.target_asset_id, request.relationship_type
    )
    return {"success": success}


@router.get("/{asset_id}/related")
async def get_related_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """Get related assets."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    related = service.get_related(asset_id)
    return {"related": related}


@router.get("/{asset_id}/history", response_model=list[HistoryResponse])
async def get_history_endpoint(
    asset_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Get asset history."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    history = service.get_history(asset_id, limit)
    return [HistoryResponse.model_validate(h) for h in history]


@router.get("/{asset_id}/collections", response_model=list[CollectionResponse])
async def get_asset_collections_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """Get collections containing an asset."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    collections = service.get_asset_collections(asset_id)
    return [CollectionResponse.model_validate(c) for c in collections]


@router.get("/stats/{project_id}", response_model=AssetStatsResponse)
async def get_stats_endpoint(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Get asset statistics."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    stats = service.get_stats(project_id)
    return AssetStatsResponse(**stats)


# ============================================================
# Collection Endpoints
# ============================================================


@router.post("/collections", response_model=CollectionResponse, status_code=201)
async def create_collection_endpoint(
    request: CollectionCreate,
    db: Session = Depends(get_db),
):
    """Create a collection."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    collection = service.create_collection(
        name=request.name,
        project_id=request.project_id,
        description=request.description,
    )
    return CollectionResponse.model_validate(collection)


@router.get("/collections/list", response_model=CollectionListResponse)
async def list_collections_endpoint(
    project_id: str | None = Query(None, description="Project ID"),
    db: Session = Depends(get_db),
):
    """List all collections."""
    collections = list_collections(db, project_id)
    return CollectionListResponse(
        collections=[CollectionResponse.model_validate(c) for c in collections],
        total=len(collections),
    )


@router.post("/collections/{collection_id}/add")
async def add_to_collection_endpoint(
    collection_id: str,
    asset_id: str = Query(..., description="Asset ID"),
    db: Session = Depends(get_db),
):
    """Add an asset to a collection."""
    from assets.collections import add_asset_to_collection
    success = add_asset_to_collection(db, collection_id, asset_id)
    return {"success": success}


@router.get("/collections/{collection_id}/assets", response_model=list[AssetResponse])
async def get_collection_assets_endpoint(
    collection_id: str,
    db: Session = Depends(get_db),
):
    """Get assets in a collection."""
    service = AssetService(db, Path(settings.STORAGE_DIR))
    assets = service.get_collection_assets(collection_id)
    return [AssetResponse.model_validate(a) for a in assets]
