"""Asset Favorites - Manage favorites, pins, and archive."""

from sqlalchemy.orm import Session

from assets.database.assets import Asset


def toggle_favorite(db: Session, asset_id: str) -> bool:
    """Toggle favorite status."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return False
    asset.is_favorite = not asset.is_favorite
    db.commit()
    return asset.is_favorite


def toggle_pin(db: Session, asset_id: str) -> bool:
    """Toggle pin status."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return False
    asset.is_pinned = not asset.is_pinned
    db.commit()
    return asset.is_pinned


def archive_asset(db: Session, asset_id: str) -> bool:
    """Archive an asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return False
    asset.is_archived = True
    asset.status = "archived"
    db.commit()
    return True


def restore_asset(db: Session, asset_id: str) -> bool:
    """Restore an archived asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return False
    asset.is_archived = False
    asset.status = "active"
    db.commit()
    return True


def hide_asset(db: Session, asset_id: str) -> bool:
    """Hide an asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return False
    asset.is_hidden = True
    db.commit()
    return True


def show_asset(db: Session, asset_id: str) -> bool:
    """Show a hidden asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return False
    asset.is_hidden = False
    db.commit()
    return True
