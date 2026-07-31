"""Asset Metadata - Extract and manage metadata."""

import json
from pathlib import Path
from typing import Optional


def extract_metadata(file_path: Path) -> dict:
    """Extract metadata from a file."""
    ext = file_path.suffix.lower()
    metadata = {
        "file_size": file_path.stat().st_size,
        "extension": ext,
        "filename": file_path.name,
    }

    # Add type-specific metadata extraction here
    # For now, return basic metadata

    return metadata


def parse_metadata_json(metadata_json: str | None) -> dict:
    """Parse metadata JSON string."""
    if not metadata_json:
        return {}
    try:
        return json.loads(metadata_json)
    except (json.JSONDecodeError, TypeError):
        return {}


def serialize_metadata(metadata: dict) -> str:
    """Serialize metadata to JSON string."""
    return json.dumps(metadata, default=str)
