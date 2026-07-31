"""Asset Collections - Group related assets."""

from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from assets.database.assets import Asset
from assets.database.collections import Collection, CollectionAsset


def create_collection(
    db: Session,
    name: str,
    project_id: str | None = None,
    description: str | None = None,
    color: str | None = None,
    icon: str | None = None,
    owner: str | None = None,
) -> Collection:
    """Create a new collection."""
    collection = Collection(
        name=name,
        project_id=project_id,
        description=description,
        color=color,
        icon=icon,
        owner=owner,
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


def get_collection(db: Session, collection_id: str) -> Collection | None:
    """Get a collection by ID."""
    return db.query(Collection).filter(Collection.id == collection_id).first()


def list_collections(
    db: Session,
    project_id: str | None = None,
) -> list[Collection]:
    """List all collections."""
    q = db.query(Collection)
    if project_id:
        q = q.filter(Collection.project_id == project_id)
    return q.order_by(desc(Collection.created_at)).all()


def update_collection(
    db: Session,
    collection_id: str,
    name: str | None = None,
    description: str | None = None,
    color: str | None = None,
    icon: str | None = None,
) -> Collection | None:
    """Update a collection."""
    collection = get_collection(db, collection_id)
    if not collection:
        return None

    if name is not None:
        collection.name = name
    if description is not None:
        collection.description = description
    if color is not None:
        collection.color = color
    if icon is not None:
        collection.icon = icon

    db.commit()
    db.refresh(collection)
    return collection


def delete_collection(db: Session, collection_id: str) -> bool:
    """Delete a collection."""
    collection = get_collection(db, collection_id)
    if not collection:
        return False
    db.delete(collection)
    db.commit()
    return True


def add_asset_to_collection(
    db: Session,
    collection_id: str,
    asset_id: str,
    sort_order: int = 0,
) -> bool:
    """Add an asset to a collection."""
    existing = (
        db.query(CollectionAsset)
        .filter(
            CollectionAsset.collection_id == collection_id,
            CollectionAsset.asset_id == asset_id,
        )
        .first()
    )
    if existing:
        return False

    ca = CollectionAsset(
        collection_id=collection_id,
        asset_id=asset_id,
        sort_order=sort_order,
    )
    db.add(ca)
    db.commit()
    return True


def remove_asset_from_collection(
    db: Session,
    collection_id: str,
    asset_id: str,
) -> bool:
    """Remove an asset from a collection."""
    ca = (
        db.query(CollectionAsset)
        .filter(
            CollectionAsset.collection_id == collection_id,
            CollectionAsset.asset_id == asset_id,
        )
        .first()
    )
    if ca:
        db.delete(ca)
        db.commit()
        return True
    return False


def get_collection_assets(
    db: Session,
    collection_id: str,
) -> list[Asset]:
    """Get all assets in a collection."""
    asset_ids = (
        db.query(CollectionAsset.asset_id)
        .filter(CollectionAsset.collection_id == collection_id)
        .order_by(CollectionAsset.sort_order)
        .all()
    )
    ids = [a[0] for a in asset_ids]
    if not ids:
        return []
    return db.query(Asset).filter(Asset.id.in_(ids)).all()


def get_asset_collections(db: Session, asset_id: str) -> list[Collection]:
    """Get all collections containing an asset."""
    collection_ids = (
        db.query(CollectionAsset.collection_id)
        .filter(CollectionAsset.asset_id == asset_id)
        .all()
    )
    ids = [c[0] for c in collection_ids]
    if not ids:
        return []
    return db.query(Collection).filter(Collection.id.in_(ids)).all()
