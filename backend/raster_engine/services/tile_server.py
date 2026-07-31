"""On-demand web-mercator tile server for arbitrary raster files.

Reads a small window from a source raster (in any CRS) and reprojects it into a
standard EPSG:3857 XYZ tile encoded as PNG. This keeps large rasters out of the
browser (the original file remains authoritative) while still allowing practical
display in the GIS workspace.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pyproj
import rasterio
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.transform import Affine
from rasterio.windows import Window
from rasterio.windows import from_bounds as window_from_bounds

WEB_MERCATOR = "EPSG:3857"
WEB_MERCATOR_EXTENT = 20037508.342789244
TILE_SIZE = 256
MAX_READ_PIXELS = 1024 * 1024


def tile_bounds(
    z: int, x: int, y: int, tile_size: int = TILE_SIZE
) -> tuple[float, float, float, float]:
    """Return (min_x, min_y, max_x, max_y) of an XYZ tile in EPSG:3857."""
    n = 2 ** z
    resolution = (2 * WEB_MERCATOR_EXTENT) / (tile_size * n)
    min_x = x * tile_size * resolution - WEB_MERCATOR_EXTENT
    max_y = WEB_MERCATOR_EXTENT - y * tile_size * resolution
    max_x = min_x + tile_size * resolution
    min_y = max_y - tile_size * resolution
    return (min_x, min_y, max_x, max_y)


def _stretch_band(band: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Percentile-stretch a band to 0-255, honoring the validity mask."""
    values = band[mask > 0]
    if values.size == 0:
        return np.zeros_like(band, dtype=np.uint8)
    p_low, p_high = np.percentile(values, (2, 98))
    if p_high - p_low < 1e-9:
        p_high = p_low + 1.0
    scaled = np.clip((band - p_low) / (p_high - p_low), 0.0, 1.0) * 255.0
    return scaled.astype(np.uint8)


def serve_tile(
    file_path: str,
    z: int,
    x: int,
    y: int,
    tile_size: int = TILE_SIZE,
    resampling: str = "bilinear",
) -> bytes | None:
    """Render a single web-mercator tile from a raster file.

    Returns raw PNG bytes, or ``None`` when the tile is outside the raster's
    extent / the file cannot be read.
    """
    try:
        src = rasterio.open(file_path)
    except Exception:
        return None

    with src:
        if src.crs is None:
            return None

        bounds = tile_bounds(z, x, y, tile_size)

        # Transform tile bounds into the source CRS.
        try:
            transformer = pyproj.Transformer.from_crs(
                WEB_MERCATOR, src.crs, always_xy=True
            )
            p1 = transformer.transform(bounds[0], bounds[1])
            p2 = transformer.transform(bounds[2], bounds[3])
        except Exception:
            return None

        src_bounds = (min(p1[0], p2[0]), min(p1[1], p2[1]), max(p1[0], p2[0]), max(p1[1], p2[1]))

        # Clip to the raster's footprint.
        left = max(src_bounds[0], src.bounds.left)
        bottom = max(src_bounds[1], src.bounds.bottom)
        right = min(src_bounds[2], src.bounds.right)
        top = min(src_bounds[3], src.bounds.top)
        if right <= left or top <= bottom:
            return None

        # Compute the source pixel window covering this tile.
        window = window_from_bounds(left, bottom, right, top, transform=src.transform)
        window = Window(
            math.floor(window.col_off),
            math.floor(window.row_off),
            math.ceil(window.width) + 2,
            math.ceil(window.height) + 2,
        )
        window = window.intersection(Window(0, 0, src.width, src.height))
        if window.width <= 0 or window.height <= 0:
            return None

        # Cap how many pixels we actually read (deep-zoom safety).
        out_w = int(window.width)
        out_h = int(window.height)
        if window.width * window.height > MAX_READ_PIXELS:
            scale = math.sqrt(MAX_READ_PIXELS / (window.width * window.height))
            out_w = max(1, int(window.width * scale))
            out_h = max(1, int(window.height * scale))

        band_count = min(src.count, 3)
        if band_count == 0:
            return None

        read_resampling = Resampling.bilinear
        try:
            data = src.read(
                list(range(1, band_count + 1)),
                window=window,
                out_shape=(band_count, out_h, out_w),
                resampling=read_resampling,
            )
            mask = src.read_masks(
                window=window,
                out_shape=(out_h, out_w),
                resampling=Resampling.nearest,
            )
        except Exception:
            return None

        if src.nodata is not None:
            nodata_mask = ~np.isclose(data, src.nodata).all(axis=0)
            mask = np.where(nodata_mask, mask, 0).astype(np.uint8)

        # Source transform adjusted for the downsampled read.
        src_transform = src.transform
        scale_x = window.width / out_w
        scale_y = window.height / out_h
        win_transform = Affine(
            src_transform.a * scale_x,
            src_transform.b * scale_y,
            src_transform.c + src_transform.a * window.col_off + src_transform.b * window.row_off,
            src_transform.d * scale_x,
            src_transform.e * scale_y,
            src_transform.f + src_transform.d * window.col_off + src_transform.e * window.row_off,
        )

        resolution = (2 * WEB_MERCATOR_EXTENT) / (2 ** z * tile_size)
        dst_transform = Affine(
            resolution, 0.0, bounds[0], 0.0, -resolution, bounds[3]
        )

        data = data.astype(np.float32)
        dst = np.zeros((band_count, tile_size, tile_size), dtype=np.float32)
        dst_mask = np.zeros((tile_size, tile_size), dtype=np.uint8)
        src_nodata = float(src.nodata) if src.nodata is not None else None

        resampling_method = (
            Resampling[resampling]
            if resampling in Resampling.__members__
            else Resampling.bilinear
        )
        try:
            rasterio.warp.reproject(
                source=data,
                destination=dst,
                src_transform=win_transform,
                src_crs=src.crs,
                src_nodata=src_nodata,
                src_resampling=resampling_method,
                dst_transform=dst_transform,
                dst_crs=WEB_MERCATOR,
                dst_nodata=0.0,
                dst_resampling=resampling_method,
            )
            rasterio.warp.reproject(
                source=mask,
                destination=dst_mask,
                src_transform=win_transform,
                src_crs=src.crs,
                src_nodata=0,
                src_resampling=Resampling.nearest,
                dst_transform=dst_transform,
                dst_crs=WEB_MERCATOR,
                dst_nodata=0,
                dst_resampling=Resampling.nearest,
            )
        except Exception:
            return None

        # Percentile stretch + RGBA assembly.
        if band_count == 1:
            rgb = _stretch_band(dst[0], dst_mask)
            rgba = np.stack([rgb, rgb, rgb], axis=0)
        else:
            rgba = np.stack(
                [
                    _stretch_band(dst[0], dst_mask),
                    _stretch_band(dst[1], dst_mask),
                    _stretch_band(dst[2], dst_mask),
                ],
                axis=0,
            )
        alpha = dst_mask.astype(np.uint8)
        rgba = np.concatenate([rgba, alpha[None, ...]], axis=0)

        try:
            with MemoryFile() as memfile:
                with memfile.open(
                    driver="PNG",
                    width=tile_size,
                    height=tile_size,
                    count=4,
                    dtype="uint8",
                ) as dst_img:
                    dst_img.write(rgba)
                return memfile.read()
        except Exception:
            return None


def tile_cache_path(cache_dir: str, raster_key: str, z: int, x: int, y: int) -> Path:
    """Return the on-disk cache path for a rendered tile."""
    return Path(cache_dir) / "raster_tiles" / raster_key / str(z) / str(x) / f"{y}.png"
