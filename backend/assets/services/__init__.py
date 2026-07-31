"""Asset Services - High-level service layer."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from assets.audit import log_action
from assets.catalog import get_asset, get_asset_stats, search_assets
from assets.collections import (
    add_asset_to_collection,
    create_collection,
    get_asset_collections,
    get_collection_assets,
    remove_asset_from_collection,
)
from assets.database.assets import Asset
from assets.database.tags import AssetTag
from assets.favorites import archive_asset, restore_asset, toggle_favorite, toggle_pin
from assets.metadata import extract_metadata, parse_metadata_json, serialize_metadata
from assets.relationships import create_relationship, get_related_assets
from assets.search import search as fast_search
from assets.utils import compute_checksum, get_asset_type, get_extension

logger = logging.getLogger("garuda.assets.service")


class AssetService:
    """High-level service for asset operations."""

    def __init__(self, db: Session, storage_root: Path):
        self.db = db
        self.storage_root = storage_root

    def create_asset(
        self,
        file_path: Path,
        project_id: str | None = None,
        name: str | None = None,
        display_name: str | None = None,
        description: str | None = None,
        asset_type: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        owner: str | None = None,
        metadata: dict | None = None,
    ) -> Asset:
        """Create a new asset from a file."""
        ext = get_extension(file_path.name)
        checksum = compute_checksum(file_path)
        file_size = file_path.stat().st_size

        # Check for duplicate
        existing = self.db.query(Asset).filter(
            Asset.checksum == checksum,
            Asset.project_id == project_id,
        ).first()
        if existing:
            logger.info(f"Duplicate detected: {file_path.name}")
            return existing

        # Generate asset ID
        asset_id = str(uuid.uuid4())

        # Store file
        assets_dir = self.storage_root / "projects" / (project_id or "default") / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        internal_name = f"{asset_id}{ext}"
        storage_path = assets_dir / internal_name

        import shutil
        shutil.copy2(str(file_path), str(storage_path))

        # Extract file metadata
        file_metadata = extract_metadata(file_path)
        if metadata:
            file_metadata.update(metadata)

        # Create asset
        asset = Asset(
            id=asset_id,
            project_id=project_id,
            name=name or file_path.stem,
            display_name=display_name,
            description=description,
            asset_type=asset_type or get_asset_type(ext),
            category=category,
            extension=ext,
            storage_path=str(storage_path),
            file_size=file_size,
            checksum=checksum,
            owner=owner,
            status="active",
            version=1,
            metadata_json=serialize_metadata(file_metadata),
            tags=json.dumps(tags) if tags else None,
            imported_at=datetime.utcnow(),
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)

        # Log action
        log_action(self.db, asset_id, "created", f"Asset created from {file_path.name}", owner)

        logger.info(f"Created asset: {asset.name} ({ext})")
        return asset

    def get(self, asset_id: str) -> Asset | None:
        """Get an asset by ID."""
        asset = get_asset(self.db, asset_id)
        if asset:
            # Update last opened
            asset.last_opened_at = datetime.utcnow()
            self.db.commit()
        return asset

    def update(
        self,
        asset_id: str,
        name: str | None = None,
        display_name: str | None = None,
        description: str | None = None,
        category: str | None = None,
        owner: str | None = None,
    ) -> Asset | None:
        """Update asset metadata."""
        asset = get_asset(self.db, asset_id)
        if not asset:
            return None

        if name is not None:
            asset.name = name
        if display_name is not None:
            asset.display_name = display_name
        if description is not None:
            asset.description = description
        if category is not None:
            asset.category = category
        if owner is not None:
            asset.owner = owner

        asset.modified_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(asset)

        log_action(self.db, asset_id, "modified", "Asset metadata updated")
        return asset

    def delete(self, asset_id: str) -> bool:
        """Delete an asset."""
        asset = get_asset(self.db, asset_id)
        if not asset:
            return False

        # Delete file
        storage_path = Path(asset.storage_path)
        if storage_path.exists():
            storage_path.unlink()

        log_action(self.db, asset_id, "deleted", f"Asset {asset.name} deleted")

        self.db.delete(asset)
        self.db.commit()
        return True

    def search(
        self,
        query: str | None = None,
        project_id: str | None = None,
        asset_type: str | None = None,
        category: str | None = None,
        extension: str | None = None,
        tags: list[str] | None = None,
        owner: str | None = None,
        favorite_only: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Asset], int]:
        """Search assets."""
        return search_assets(
            db=self.db,
            project_id=project_id,
            query=query,
            asset_type=asset_type,
            category=category,
            extension=extension,
            tags=tags,
            owner=owner,
            favorite_only=favorite_only,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=offset,
            limit=limit,
        )

    def fast_search(self, query: str, project_id: str | None = None) -> list[Asset]:
        """Fast search."""
        return fast_search(self.db, query, project_id)

    def toggle_favorite(self, asset_id: str) -> bool:
        """Toggle favorite status."""
        result = toggle_favorite(self.db, asset_id)
        if result:
            action = "favorited" if result else "unfavorited"
            log_action(self.db, asset_id, action)
        return result

    def toggle_pin(self, asset_id: str) -> bool:
        """Toggle pin status."""
        return toggle_pin(self.db, asset_id)

    def archive(self, asset_id: str) -> bool:
        """Archive an asset."""
        result = archive_asset(self.db, asset_id)
        if result:
            log_action(self.db, asset_id, "archived")
        return result

    def restore(self, asset_id: str) -> bool:
        """Restore an archived asset."""
        result = restore_asset(self.db, asset_id)
        if result:
            log_action(self.db, asset_id, "restored")
        return result

    def add_tag(self, asset_id: str, tag: str) -> bool:
        """Add a tag to an asset."""
        existing = (
            self.db.query(AssetTag)
            .filter(AssetTag.asset_id == asset_id, AssetTag.tag == tag)
            .first()
        )
        if existing:
            return False

        tag_entry = AssetTag(asset_id=asset_id, tag=tag)
        self.db.add(tag_entry)
        self.db.commit()
        return True

    def remove_tag(self, asset_id: str, tag: str) -> bool:
        """Remove a tag from an asset."""
        tag_entry = (
            self.db.query(AssetTag)
            .filter(AssetTag.asset_id == asset_id, AssetTag.tag == tag)
            .first()
        )
        if tag_entry:
            self.db.delete(tag_entry)
            self.db.commit()
            return True
        return False

    def get_tags(self, asset_id: str) -> list[str]:
        """Get tags for an asset."""
        tags = (
            self.db.query(AssetTag.tag)
            .filter(AssetTag.asset_id == asset_id)
            .all()
        )
        return [t[0] for t in tags]

    def create_relationship(
        self,
        source_asset_id: str,
        target_asset_id: str,
        relationship_type: str,
    ) -> bool:
        """Create a relationship between assets."""
        create_relationship(self.db, source_asset_id, target_asset_id, relationship_type)
        return True

    def get_related(self, asset_id: str) -> list[dict]:
        """Get related assets."""
        return get_related_assets(self.db, asset_id)

    def create_collection(
        self,
        name: str,
        project_id: str | None = None,
        description: str | None = None,
    ):
        """Create a collection."""
        return create_collection(self.db, name, project_id, description)

    def add_to_collection(self, collection_id: str, asset_id: str) -> bool:
        """Add asset to collection."""
        return add_asset_to_collection(self.db, collection_id, asset_id)

    def remove_from_collection(self, collection_id: str, asset_id: str) -> bool:
        """Remove asset from collection."""
        return remove_asset_from_collection(self.db, collection_id, asset_id)

    def get_collection_assets(self, collection_id: str) -> list[Asset]:
        """Get assets in a collection."""
        return get_collection_assets(self.db, collection_id)

    def get_asset_collections(self, asset_id: str) -> list:
        """Get collections containing an asset."""
        return get_asset_collections(self.db, asset_id)

    def get_stats(self, project_id: str | None = None) -> dict:
        """Get asset statistics."""
        return get_asset_stats(self.db, project_id)

    def get_history(self, asset_id: str, limit: int = 50) -> list:
        """Get asset history."""
        from assets.audit import get_asset_history
        return get_asset_history(self.db, asset_id, limit)

    def set_metadata(self, asset_id: str, key: str, value: str) -> bool:
        """Set metadata for an asset."""
        asset = get_asset(self.db, asset_id)
        if not asset:
            return False

        metadata = parse_metadata_json(asset.metadata_json)
        metadata[key] = value
        asset.metadata_json = serialize_metadata(metadata)
        self.db.commit()
        return True

    def get_metadata(self, asset_id: str) -> dict:
        """Get metadata for an asset."""
        asset = get_asset(self.db, asset_id)
        if not asset:
            return {}
        return parse_metadata_json(asset.metadata_json)
