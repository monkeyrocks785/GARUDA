"""Asset Audit - Track all actions on assets."""

from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from assets.database.history import AssetHistory


def log_action(
    db: Session,
    asset_id: str,
    action: str,
    details: str | None = None,
    performed_by: str | None = None,
) -> AssetHistory:
    """Log an action on an asset."""
    entry = AssetHistory(
        asset_id=asset_id,
        action=action,
        details=details,
        performed_by=performed_by,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_asset_history(
    db: Session,
    asset_id: str,
    limit: int = 50,
) -> list[AssetHistory]:
    """Get history for an asset."""
    return (
        db.query(AssetHistory)
        .filter(AssetHistory.asset_id == asset_id)
        .order_by(desc(AssetHistory.timestamp))
        .limit(limit)
        .all()
    )


def get_recent_actions(
    db: Session,
    project_id: str | None = None,
    limit: int = 20,
) -> list[AssetHistory]:
    """Get recent actions across all assets."""
    from assets.database.assets import Asset

    q = (
        db.query(AssetHistory)
        .join(Asset, AssetHistory.asset_id == Asset.id)
    )
    if project_id:
        q = q.filter(Asset.project_id == project_id)
    return q.order_by(desc(AssetHistory.timestamp)).limit(limit).all()
