"""Asset Catalog - Search, filter, and organize assets."""

from typing import Optional

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from assets.database.assets import Asset
from assets.database.tags import AssetTag


def search_assets(
    db: Session,
    project_id: str | None = None,
    query: str | None = None,
    asset_type: str | None = None,
    category: str | None = None,
    extension: str | None = None,
    status: str | None = None,
    tags: list[str] | None = None,
    owner: str | None = None,
    favorite_only: bool = False,
    pinned_only: bool = False,
    archived_only: bool = False,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Asset], int]:
    """Search assets with filters."""
    q = db.query(Asset)

    # Project filter
    if project_id:
        q = q.filter(Asset.project_id == project_id)

    # Text search
    if query:
        search = f"%{query}%"
        q = q.filter(
            or_(
                Asset.name.ilike(search),
                Asset.display_name.ilike(search),
                Asset.description.ilike(search),
                Asset.original_filename.ilike(search) if hasattr(Asset, 'original_filename') else Asset.name.ilike(search),
            )
        )

    # Type filters
    if asset_type:
        q = q.filter(Asset.asset_type == asset_type)
    if category:
        q = q.filter(Asset.category == category)
    if extension:
        q = q.filter(Asset.extension == extension)
    if status:
        q = q.filter(Asset.status == status)
    if owner:
        q = q.filter(Asset.owner == owner)

    # Favorites
    if favorite_only:
        q = q.filter(Asset.is_favorite == True)

    # Pinned
    if pinned_only:
        q = q.filter(Asset.is_pinned == True)

    # Archived
    if archived_only:
        q = q.filter(Asset.is_archived == True)
    else:
        q = q.filter(Asset.is_archived == False)

    # Hidden
    q = q.filter(Asset.is_hidden == False)

    # Tag filter
    if tags:
        tag_subq = (
            db.query(AssetTag.asset_id)
            .filter(AssetTag.tag.in_(tags))
            .subquery()
        )
        q = q.filter(Asset.id.in_(tag_subq))

    # Count total
    total = q.count()

    # Sort
    sort_column = getattr(Asset, sort_by, Asset.created_at)
    if sort_order == "desc":
        q = q.order_by(desc(sort_column))
    else:
        q = q.order_by(sort_column)

    # Paginate
    assets = q.offset(offset).limit(limit).all()

    return assets, total


def get_asset(db: Session, asset_id: str) -> Asset | None:
    """Get a single asset by ID."""
    return db.query(Asset).filter(Asset.id == asset_id).first()


def get_assets_by_project(db: Session, project_id: str) -> list[Asset]:
    """Get all assets for a project."""
    return (
        db.query(Asset)
        .filter(Asset.project_id == project_id, Asset.is_archived == False)
        .order_by(desc(Asset.created_at))
        .all()
    )


def get_recent_assets(db: Session, project_id: str | None = None, limit: int = 10) -> list[Asset]:
    """Get recently imported assets."""
    q = db.query(Asset).filter(Asset.is_archived == False)
    if project_id:
        q = q.filter(Asset.project_id == project_id)
    return q.order_by(desc(Asset.imported_at)).limit(limit).all()


def get_favorite_assets(db: Session, project_id: str | None = None) -> list[Asset]:
    """Get favorite assets."""
    q = db.query(Asset).filter(Asset.is_favorite == True, Asset.is_archived == False)
    if project_id:
        q = q.filter(Asset.project_id == project_id)
    return q.order_by(desc(Asset.modified_at)).all()


def get_assets_by_type(db: Session, asset_type: str, project_id: str | None = None) -> list[Asset]:
    """Get all assets of a specific type."""
    q = db.query(Asset).filter(Asset.asset_type == asset_type, Asset.is_archived == False)
    if project_id:
        q = q.filter(Asset.project_id == project_id)
    return q.order_by(desc(Asset.created_at)).all()


def get_asset_stats(db: Session, project_id: str | None = None) -> dict:
    """Get asset statistics."""
    q = db.query(Asset).filter(Asset.is_archived == False)
    if project_id:
        q = q.filter(Asset.project_id == project_id)

    total = q.count() or 0

    by_type = dict(
        db.query(Asset.asset_type, func.count(Asset.id))
        .filter(Asset.is_archived == False)
        .group_by(Asset.asset_type)
        .all()
    )

    by_category = dict(
        db.query(Asset.category, func.count(Asset.id))
        .filter(Asset.is_archived == False, Asset.category.isnot(None))
        .group_by(Asset.category)
        .all()
    )

    total_size = db.query(func.sum(Asset.file_size)).filter(
        Asset.is_archived == False
    ).scalar() or 0

    return {
        "total": total,
        "by_type": by_type,
        "by_category": by_category,
        "total_size_bytes": total_size,
    }
