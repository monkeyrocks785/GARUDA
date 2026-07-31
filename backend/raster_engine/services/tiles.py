"""Tile generation for rasters."""

import math
from pathlib import Path

import rasterio
from rasterio.windows import Window

from raster_engine.config import DEFAULT_TILE_SIZE


def generate_tiles(
    file_path: str,
    output_dir: str,
    tile_size: int = DEFAULT_TILE_SIZE,
    zoom_levels: list[int] | None = None,
) -> dict:
    """Generate tiles from a raster file.

    Args:
        file_path: Input raster path.
        output_dir: Directory to write tiles.
        tile_size: Tile dimensions in pixels.
        zoom_levels: Zoom levels to generate.

    Returns:
        dict with tile info.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with rasterio.open(file_path) as src:
        width = src.width
        height = src.height

        # Calculate zoom levels if not provided
        if zoom_levels is None:
            max_zoom = max(1, int(math.log2(max(width, height) / tile_size)))
            zoom_levels = list(range(0, max_zoom + 1))

        tiles_generated = 0

        for zoom in zoom_levels:
            # Calculate dimensions at this zoom level
            scale = 2 ** zoom
            zoom_width = max(1, width // scale)
            zoom_height = max(1, height // scale)

            # Number of tiles
            n_cols = math.ceil(zoom_width / tile_size)
            n_rows = math.ceil(zoom_height / tile_size)

            zoom_dir = output_path / str(zoom)
            zoom_dir.mkdir(exist_ok=True)

            for row in range(n_rows):
                for col in range(n_cols):
                    # Window in source raster
                    x_off = col * tile_size * scale
                    y_off = row * tile_size * scale
                    x_size = min(tile_size * scale, width - x_off)
                    y_size = min(tile_size * scale, height - y_off)

                    if x_size <= 0 or y_size <= 0:
                        continue

                    window = Window(x_off, y_off, x_size, y_size)
                    data = src.read(window=window)

                    # Write tile
                    tile_path = zoom_dir / f"{col}_{row}.tif"
                    tile_profile = src.profile.copy()
                    tile_profile.update(
                        width=x_size,
                        height=y_size,
                        transform=rasterio.windows.transform(window, src.transform),
                    )

                    with rasterio.open(tile_path, "w", **tile_profile) as tile_dst:
                        tile_dst.write(data)
                    tiles_generated += 1

        return {
            "tiles_generated": tiles_generated,
            "zoom_levels": zoom_levels,
            "tile_size": tile_size,
            "output_dir": str(output_path),
        }
