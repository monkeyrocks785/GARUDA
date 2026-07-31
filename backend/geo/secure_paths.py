"""Path security helpers - restrict file access to configured GARUDA locations."""

from __future__ import annotations

from pathlib import Path

from config.settings import settings


def allowed_roots() -> list[Path]:
    """Return the resolved set of configured GARUDA data locations."""
    raw = [
        settings.STORAGE_DIR,
        settings.PROJECTS_DIR,
        settings.TILES_DIR,
        settings.BASEMAPS_DIR,
        settings.MODELS_DIR,
        settings.EXPORT_DIR,
    ]
    return [Path(p).resolve() for p in raw]


def is_allowed_location(candidate: str | Path) -> bool:
    """Return True if the candidate path is inside a configured data location."""
    resolved = Path(candidate).resolve()
    return any(resolved == root or root in resolved.parents for root in allowed_roots())
