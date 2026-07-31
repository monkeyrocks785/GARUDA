"""Asset Relationships - Track relationships between assets."""

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from assets.database.relationships import AssetRelationship


def create_relationship(
    db: Session,
    source_asset_id: str,
    target_asset_id: str,
    relationship_type: str,
    metadata_json: str | None = None,
) -> AssetRelationship:
    """Create a relationship between two assets."""
    # Check for existing relationship
    existing = (
        db.query(AssetRelationship)
        .filter(
            AssetRelationship.source_asset_id == source_asset_id,
            AssetRelationship.target_asset_id == target_asset_id,
            AssetRelationship.relationship_type == relationship_type,
        )
        .first()
    )

    if existing:
        return existing

    rel = AssetRelationship(
        source_asset_id=source_asset_id,
        target_asset_id=target_asset_id,
        relationship_type=relationship_type,
        metadata_json=metadata_json,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


def get_relationships(
    db: Session,
    asset_id: str,
    relationship_type: str | None = None,
) -> list[AssetRelationship]:
    """Get all relationships for an asset."""
    q = db.query(AssetRelationship).filter(
        or_(
            AssetRelationship.source_asset_id == asset_id,
            AssetRelationship.target_asset_id == asset_id,
        )
    )
    if relationship_type:
        q = q.filter(AssetRelationship.relationship_type == relationship_type)
    return q.all()


def get_related_assets(
    db: Session,
    asset_id: str,
    relationship_type: str | None = None,
) -> list[dict]:
    """Get related assets with their details."""
    from assets.catalog import get_asset

    relationships = get_relationships(db, asset_id, relationship_type)
    result = []

    for rel in relationships:
        if rel.source_asset_id == asset_id:
            related_id = rel.target_asset_id
            direction = "outgoing"
        else:
            related_id = rel.source_asset_id
            direction = "incoming"

        related_asset = get_asset(db, related_id)
        if related_asset:
            result.append({
                "asset": related_asset,
                "relationship_type": rel.relationship_type,
                "direction": direction,
                "relationship_id": rel.id,
            })

    return result


def delete_relationship(db: Session, relationship_id: str) -> bool:
    """Delete a relationship."""
    rel = db.query(AssetRelationship).filter(AssetRelationship.id == relationship_id).first()
    if rel:
        db.delete(rel)
        db.commit()
        return True
    return False
