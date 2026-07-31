"""Data Engine importers - Import datasets from various sources."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from data_engine.config import ALL_EXTENSIONS
from data_engine.database.datasets import Dataset
from data_engine.metadata import extract_metadata
from data_engine.storage import store_file
from data_engine.utils import (
    compute_checksum,
    get_dataset_type,
    get_file_extension,
    sanitize_filename,
)
from data_engine.validators import validate_dataset
from data_engine.versioning import check_duplicate, create_version, find_existing_by_name

logger = logging.getLogger("garuda.data_engine.importer")


class ImportResult:
    """Result of an import operation."""

    def __init__(self):
        self.success = True
        self.dataset_id: str | None = None
        self.version: int = 1
        self.is_duplicate: bool = False
        self.is_new_version: bool = False
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "dataset_id": self.dataset_id,
            "version": self.version,
            "is_duplicate": self.is_duplicate,
            "is_new_version": self.is_new_version,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def import_file(
    db: Session,
    file_path: Path,
    project_id: str,
    storage_root: Path,
    name: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    imported_by: str | None = None,
) -> ImportResult:
    """Import a single file as a dataset."""
    result = ImportResult()

    # Validate
    validation = validate_dataset(file_path)
    if not validation.is_valid:
        result.success = False
        result.errors = validation.errors
        return result

    result.warnings = validation.warnings

    # Compute checksum
    checksum = compute_checksum(file_path)

    # Check for duplicate by checksum
    existing = check_duplicate(db, checksum, project_id)
    if existing:
        result.is_duplicate = True
        result.dataset_id = existing.id
        result.version = existing.version
        logger.info(f"Duplicate detected: {file_path.name} (checksum: {checksum[:16]}...)")
        return result

    # Check for new version (same name, different content)
    dataset_name = name or file_path.stem
    existing_by_name = find_existing_by_name(db, dataset_name, project_id)

    # Extract metadata
    metadata = extract_metadata(file_path)

    # Generate dataset ID
    import uuid
    dataset_id = str(uuid.uuid4())

    # Store file
    internal_filename = f"{dataset_id}{file_path.suffix}"
    storage_path = store_file(file_path, project_id, dataset_id, storage_root)

    if existing_by_name:
        # Create new version
        version_entry = create_version(
            db=db,
            dataset=existing_by_name,
            checksum=checksum,
            file_size=file_path.stat().st_size,
            storage_path=str(storage_path),
            internal_filename=internal_filename,
            change_description="Updated content",
        )
        result.is_new_version = True
        result.version = version_entry.version_number
        result.dataset_id = existing_by_name.id
        logger.info(f"New version created for {dataset_name}: v{version_entry.version_number}")
    else:
        # Create new dataset
        bounds = metadata.get("bounds")
        dataset = Dataset(
            id=dataset_id,
            project_id=project_id,
            name=dataset_name,
            description=description,
            dataset_type=get_dataset_type(file_path.suffix),
            original_filename=file_path.name,
            internal_filename=internal_filename,
            extension=file_path.suffix.lower(),
            coordinate_system=metadata.get("crs"),
            bbox_min_x=bounds.get("min_x") if bounds else None,
            bbox_min_y=bounds.get("min_y") if bounds else None,
            bbox_max_x=bounds.get("max_x") if bounds else None,
            bbox_max_y=bounds.get("max_y") if bounds else None,
            resolution_x=metadata.get("pixel_size_x"),
            resolution_y=metadata.get("pixel_size_y"),
            bands=metadata.get("bands"),
            width=metadata.get("width"),
            height=metadata.get("height"),
            file_size=file_path.stat().st_size,
            checksum=checksum,
            status="ready",
            version=1,
            source="import",
            imported_by=imported_by,
            storage_path=str(storage_path),
            metadata_json=json.dumps(metadata),
            tags=json.dumps(tags) if tags else None,
            imported_at=datetime.utcnow(),
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        result.dataset_id = dataset.id
        result.version = 1
        logger.info(f"Imported: {dataset_name} ({file_path.suffix})")

    return result


def import_folder(
    db: Session,
    folder_path: Path,
    project_id: str,
    storage_root: Path,
    recursive: bool = True,
    imported_by: str | None = None,
) -> list[ImportResult]:
    """Import all supported files from a folder."""
    results = []

    if not folder_path.exists() or not folder_path.is_dir():
        result = ImportResult()
        result.success = False
        result.errors.append(f"Folder not found: {folder_path}")
        return [results]

    pattern = "**/*" if recursive else "*"
    for file_path in folder_path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in ALL_EXTENSIONS:
            result = import_file(
                db=db,
                file_path=file_path,
                project_id=project_id,
                storage_root=storage_root,
                imported_by=imported_by,
            )
            results.append(result)

    return results


def import_multiple(
    db: Session,
    file_paths: list[Path],
    project_id: str,
    storage_root: Path,
    imported_by: str | None = None,
) -> list[ImportResult]:
    """Import multiple files."""
    results = []
    for file_path in file_paths:
        result = import_file(
            db=db,
            file_path=file_path,
            project_id=project_id,
            storage_root=storage_root,
            imported_by=imported_by,
        )
        results.append(result)
    return results
