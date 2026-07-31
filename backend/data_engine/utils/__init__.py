"""Data Engine utility functions."""

import hashlib
from pathlib import Path


def compute_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute checksum of a file."""
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension."""
    return Path(filename).suffix.lower()


def get_dataset_type(extension: str) -> str:
    """Determine dataset type from extension."""
    from data_engine.config import EXTENSION_TYPE_MAP
    return EXTENSION_TYPE_MAP.get(extension, "other")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    name = Path(filename).stem
    ext = Path(filename).suffix
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = name.strip('._')
    return f"{name}{ext}"


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
