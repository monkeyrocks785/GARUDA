"""Asset Search - Fast search implementation."""

from typing import Optional

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from assets.database.assets import Asset
from assets.database.tags import AssetTag


def search(
    db: Session,
    query: str,
    project_id: str | None = None,
    asset_type: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    owner: str | None = None,
    limit: int = 50,
) -> list[Asset]:
    """Fast search across assets."""
    q = db.query(Asset).filter(Asset.is_archived == False, Asset.is_hidden == False)

    # Text search across multiple fields
    search = f"%{query}%"
    q = q.filter(
        or_(
            Asset.name.ilike(search),
            Asset.display_name.ilike(search),
            Asset.description.ilike(search),
        )
    )

    # Filters
    if project_id:
        q = q.filter(Asset.project_id == project_id)
    if asset_type:
        q = q.filter(Asset.asset_type == asset_type)
    if category:
        q = q.filter(Asset.category == category)
    if owner:
        q = q.filter(Asset.owner == owner)

    # Tag filter
    if tags:
        tag_subq = (
            db.query(AssetTag.asset_id)
            .filter(AssetTag.tag.in_(tags))
            .subquery()
        )
        q = q.filter(Asset.id.in_(tag_subq))

    return q.order_by(desc(Asset.created_at)).limit(limit).all()


def search_metadata(
    db: Session,
    key: str,
    value: str,
    project_id: str | None = None,
) -> list[Asset]:
    """Search by metadata key-value pair."""
    q = db.query(Asset).filter(
        Asset.is_archived == False,
        Asset.metadata_json.ilike(f'%"{key}": "%{value}%"%'),
    )
    if project_id:
        q = q.filter(Asset.project_id == project_id)
    return q.order_by(desc(Asset.created_at)).all()
