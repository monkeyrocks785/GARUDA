"""Data Engine services - High-level service layer."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from data_engine.catalog import (
    add_tag,
    get_dataset,
    get_dataset_stats,
    get_dataset_tags,
    get_datasets_by_type,
    get_favorite_datasets,
    get_recent_datasets,
    remove_tag,
    search_datasets,
    toggle_favorite,
)
from data_engine.database.datasets import Dataset
from data_engine.database.metadata import DatasetMetadata
from data_engine.importers import ImportResult, import_file, import_folder, import_multiple
from data_engine.storage import delete_stored_file, get_storage_usage
from data_engine.versioning import get_version_history

logger = logging.getLogger("garuda.data_engine.service")


class DatasetService:
    """High-level service for dataset operations."""

    def __init__(self, db: Session, storage_root: Path):
        self.db = db
        self.storage_root = storage_root

    def import_file(
        self,
        file_path: Path,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        imported_by: str | None = None,
    ) -> ImportResult:
        """Import a single file."""
        return import_file(
            db=self.db,
            file_path=file_path,
            project_id=project_id,
            storage_root=self.storage_root,
            name=name,
            description=description,
            tags=tags,
            imported_by=imported_by,
        )

    def import_folder(
        self,
        folder_path: Path,
        project_id: str,
        recursive: bool = True,
        imported_by: str | None = None,
    ) -> list[ImportResult]:
        """Import all files from a folder."""
        return import_folder(
            db=self.db,
            folder_path=folder_path,
            project_id=project_id,
            storage_root=self.storage_root,
            recursive=recursive,
            imported_by=imported_by,
        )

    def import_multiple(
        self,
        file_paths: list[Path],
        project_id: str,
        imported_by: str | None = None,
    ) -> list[ImportResult]:
        """Import multiple files."""
        return import_multiple(
            db=self.db,
            file_paths=file_paths,
            project_id=project_id,
            storage_root=self.storage_root,
            imported_by=imported_by,
        )

    def search(
        self,
        project_id: str,
        query: str | None = None,
        dataset_type: str | None = None,
        extension: str | None = None,
        tags: list[str] | None = None,
        favorite_only: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Dataset], int]:
        """Search datasets."""
        return search_datasets(
            db=self.db,
            project_id=project_id,
            query=query,
            dataset_type=dataset_type,
            extension=extension,
            tags=tags,
            favorite_only=favorite_only,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=offset,
            limit=limit,
        )

    def get(self, dataset_id: str) -> Dataset | None:
        """Get a dataset by ID."""
        return get_dataset(self.db, dataset_id)

    def update(
        self,
        dataset_id: str,
        name: str | None = None,
        description: str | None = None,
        notes: str | None = None,
    ) -> Dataset | None:
        """Update dataset metadata."""
        dataset = get_dataset(self.db, dataset_id)
        if not dataset:
            return None

        if name is not None:
            dataset.name = name
        if description is not None:
            dataset.description = description
        if notes is not None:
            dataset.notes = notes

        dataset.modified_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def delete(self, dataset_id: str) -> bool:
        """Delete a dataset."""
        dataset = get_dataset(self.db, dataset_id)
        if not dataset:
            return False

        # Delete stored file
        storage_path = Path(dataset.storage_path)
        delete_stored_file(storage_path)

        # Delete from database
        self.db.delete(dataset)
        self.db.commit()
        logger.info(f"Deleted dataset: {dataset.name}")
        return True

    def toggle_favorite(self, dataset_id: str) -> bool:
        """Toggle favorite status."""
        return toggle_favorite(self.db, dataset_id)

    def add_tag(self, dataset_id: str, tag: str) -> bool:
        """Add a tag."""
        return add_tag(self.db, dataset_id, tag)

    def remove_tag(self, dataset_id: str, tag: str) -> bool:
        """Remove a tag."""
        return remove_tag(self.db, dataset_id, tag)

    def get_tags(self, dataset_id: str) -> list[str]:
        """Get tags for a dataset."""
        return get_dataset_tags(self.db, dataset_id)

    def get_version_history(self, dataset_id: str) -> list[dict]:
        """Get version history."""
        versions = get_version_history(self.db, dataset_id)
        return [
            {
                "id": v.id,
                "version_number": v.version_number,
                "checksum": v.checksum,
                "file_size": v.file_size,
                "change_description": v.change_description,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ]

    def get_stats(self, project_id: str) -> dict:
        """Get dataset statistics."""
        return get_dataset_stats(self.db, project_id)

    def get_recent(self, project_id: str, limit: int = 10) -> list[Dataset]:
        """Get recent datasets."""
        return get_recent_datasets(self.db, project_id, limit)

    def get_favorites(self, project_id: str) -> list[Dataset]:
        """Get favorite datasets."""
        return get_favorite_datasets(self.db, project_id)

    def get_by_type(self, project_id: str, dataset_type: str) -> list[Dataset]:
        """Get datasets by type."""
        return get_datasets_by_type(self.db, project_id, dataset_type)

    def get_storage_usage(self, project_id: str) -> dict:
        """Get storage usage."""
        return get_storage_usage(project_id, self.storage_root)

    def set_metadata(self, dataset_id: str, key: str, value: str, category: str = "general") -> bool:
        """Set metadata for a dataset."""
        dataset = get_dataset(self.db, dataset_id)
        if not dataset:
            return False

        existing = (
            self.db.query(DatasetMetadata)
            .filter(
                DatasetMetadata.dataset_id == dataset_id,
                DatasetMetadata.key == key,
            )
            .first()
        )

        if existing:
            existing.value = value
            existing.category = category
        else:
            meta = DatasetMetadata(
                dataset_id=dataset_id,
                key=key,
                value=value,
                category=category,
            )
            self.db.add(meta)

        self.db.commit()
        return True

    def get_metadata(self, dataset_id: str) -> dict:
        """Get all metadata for a dataset."""
        metas = (
            self.db.query(DatasetMetadata)
            .filter(DatasetMetadata.dataset_id == dataset_id)
            .all()
        )
        return {m.key: {"value": m.value, "category": m.category} for m in metas}
