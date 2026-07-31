"""Data Engine storage - Manage dataset file storage."""

import shutil
from pathlib import Path
from typing import Optional

from data_engine.config import DATASETS_SUBDIR, THUMBNAILS_SUBDIR
from data_engine.utils import sanitize_filename


def get_datasets_dir(project_id: str, storage_root: Path) -> Path:
    """Get datasets directory for a project."""
    datasets_dir = storage_root / "projects" / project_id / DATASETS_SUBDIR
    datasets_dir.mkdir(parents=True, exist_ok=True)
    return datasets_dir


def get_thumbnails_dir(project_id: str, storage_root: Path) -> Path:
    """Get thumbnails directory for a project."""
    thumb_dir = storage_root / "projects" / project_id / THUMBNAILS_SUBDIR
    thumb_dir.mkdir(parents=True, exist_ok=True)
    return thumb_dir


def generate_internal_filename(original_filename: str, dataset_id: str) -> str:
    """Generate internal filename to avoid conflicts."""
    ext = Path(original_filename).suffix
    return f"{dataset_id}{ext}"


def store_file(
    source_path: Path,
    project_id: str,
    dataset_id: str,
    storage_root: Path,
) -> Path:
    """Copy file to project storage.

    Original files are NEVER modified. We always copy.
    """
    datasets_dir = get_datasets_dir(project_id, storage_root)
    internal_name = generate_internal_filename(source_path.name, dataset_id)
    dest_path = datasets_dir / internal_name

    shutil.copy2(str(source_path), str(dest_path))
    return dest_path


def delete_stored_file(storage_path: Path) -> bool:
    """Delete a stored file."""
    try:
        if storage_path.exists():
            storage_path.unlink()
            return True
    except Exception:
        pass
    return False


def get_storage_usage(project_id: str, storage_root: Path) -> dict:
    """Get storage usage for a project."""
    datasets_dir = storage_root / "projects" / project_id / DATASETS_SUBDIR
    if not datasets_dir.exists():
        return {"total_bytes": 0, "file_count": 0}

    total = 0
    count = 0
    for f in datasets_dir.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
            count += 1

    return {"total_bytes": total, "file_count": count}
