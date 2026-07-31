"""Asset Indexer - Index assets for fast search."""

from sqlalchemy.orm import Session

from assets.database.assets import Asset


def index_asset(db: Session, asset_id: str) -> dict:
    """Index a single asset for search."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return {"error": "Asset not found"}

    # Update status to active (indexed)
    if asset.status == "processing":
        asset.status = "active"
        db.commit()

    return {
        "id": asset.id,
        "name": asset.name,
        "type": asset.asset_type,
        "status": "indexed",
    }


def index_project_assets(db: Session, project_id: str) -> dict:
    """Index all assets in a project."""
    assets = db.query(Asset).filter(
        Asset.project_id == project_id,
        Asset.status == "processing",
    ).all()

    indexed = 0
    for asset in assets:
        asset.status = "active"
        indexed += 1

    db.commit()

    return {"indexed": indexed}
