"""Offline basemap service - local XYZ tile folders and registered GeoTIFFs.

GARUDA is fully offline-first: no online tile providers are used. Local XYZ tile
folders are auto-discovered from the configured tiles directory, and GeoTIFF
files can be registered (paths are restricted to configured data locations).
"""

from __future__ import annotations

import re
from pathlib import Path

import rasterio
from loguru import logger
from sqlalchemy.orm import Session

from config.settings import settings
from geo.secure_paths import is_allowed_location
from models.gis_basemap import GisBasemap
from raster_engine.services.tile_server import serve_tile

BLANK_GRID_ID = "blank_grid"
XYZ_PREFIX = "xyz"

TILE_URL_TEMPLATE = "/api/v1/gis/basemaps/{basemap_id}/tiles/{{z}}/{{x}}/{{y}}.png"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "basemap"


def _tiles_root() -> Path:
    return Path(settings.TILES_DIR).resolve()


def _is_within(root: Path, candidate: Path) -> bool:
    resolved = candidate.resolve()
    return resolved == root or root in resolved.parents


def blank_grid_basemap() -> dict:
    return {
        "id": BLANK_GRID_ID,
        "name": "Blank Grid",
        "basemap_type": "blank",
        "crs": "EPSG:3857",
        "tile_url_template": "",
    }


def discover_xyz_basemaps() -> list[dict]:
    """Auto-discover local XYZ tile folders (``{z}/{x}/{y}.png`` layout)."""
    root = _tiles_root()
    basemaps: list[dict] = []
    if not root.exists():
        return basemaps

    for folder in sorted(root.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        probe = folder / "1" / "0" / "0.png"
        if not probe.is_file():
            continue
        basemap_id = f"{XYZ_PREFIX}-{_slug(folder.name)}"
        basemaps.append(
            {
                "id": basemap_id,
                "name": folder.name,
                "basemap_type": "xyz_dir",
                "crs": "EPSG:3857",
                "tile_url_template": TILE_URL_TEMPLATE.format(basemap_id=basemap_id),
            }
        )
    return basemaps


def list_registered_basemaps(db: Session) -> list[dict]:
    basemaps = db.query(GisBasemap).order_by(GisBasemap.created_at).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "basemap_type": b.basemap_type,
            "crs": b.crs,
            "tile_url_template": TILE_URL_TEMPLATE.format(basemap_id=b.id),
        }
        for b in basemaps
    ]


def list_basemaps(db: Session) -> list[dict]:
    return [blank_grid_basemap(), *discover_xyz_basemaps(), *list_registered_basemaps(db)]


def register_geotiff_basemap(
    db: Session, name: str, path: str
) -> GisBasemap:
    """Register a GeoTIFF (or other raster) as an offline basemap.

    Raises:
        ValueError: If the path is outside configured data locations or invalid.
    """
    candidate = Path(path).resolve()
    if not is_allowed_location(candidate):
        raise ValueError("Basemap path must be inside the configured storage directory")
    if not candidate.is_file():
        raise ValueError("Basemap file not found")

    try:
        with rasterio.open(candidate):
            pass
    except Exception as e:
        raise ValueError(f"Invalid or corrupt raster basemap: {e}") from e

    existing = (
        db.query(GisBasemap)
        .filter(GisBasemap.path == str(candidate))
        .first()
    )
    if existing:
        return existing

    basemap = GisBasemap(
        name=name,
        basemap_type="geotiff",
        path=str(candidate),
        crs=None,
    )
    db.add(basemap)
    db.commit()
    db.refresh(basemap)
    logger.info("GeoTIFF basemap registered", basemap_id=basemap.id, name=name)
    return basemap


def delete_basemap(db: Session, basemap_id: str) -> bool:
    basemap = db.query(GisBasemap).filter(GisBasemap.id == basemap_id).first()
    if not basemap:
        return False
    db.delete(basemap)
    db.commit()
    return True


def serve_xyz_tile(basemap_id: str, z: int, x: int, y: int) -> bytes | None:
    """Serve a PNG tile from a local XYZ folder (path-traversal safe)."""
    if not basemap_id.startswith(f"{XYZ_PREFIX}-"):
        return None
    slug = basemap_id[len(f"{XYZ_PREFIX}-"):]
    root = _tiles_root()
    if not root.exists():
        return None

    folder = next(
        (c for c in root.iterdir() if c.is_dir() and _slug(c.name) == slug),
        None,
    )
    if folder is None:
        return None
    folder = folder.resolve()
    if not _is_within(root, folder) or not folder.is_dir():
        return None

    tile = (folder / str(z) / str(x) / f"{y}.png").resolve()
    if not _is_within(folder, tile) or not tile.is_file():
        return None

    try:
        return tile.read_bytes()
    except OSError:
        return None


def serve_registered_tile(
    db: Session, basemap_id: str, z: int, x: int, y: int
) -> bytes | None:
    """Serve a PNG tile from a registered GeoTIFF basemap."""
    basemap = db.query(GisBasemap).filter(GisBasemap.id == basemap_id).first()
    if not basemap:
        return None
    return serve_tile(basemap.path, z, x, y)
