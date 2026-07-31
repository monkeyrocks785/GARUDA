"""Raster Processing Engine services."""

from .bands import extract_bands, select_single_band
from .clip import clip_raster_with_aoi, clip_raster_with_polygon, clip_raster_with_rectangle
from .crop import crop_raster
from .mosaic import mosaic_rasters
from .nodata import fill_nodata, set_nodata
from .overview import build_overviews, get_overview_levels, has_overviews
from .raster_io import (
    calculate_histogram,
    calculate_statistics,
    get_raster_info,
    open_raster,
    read_metadata,
    save_metadata_to_db,
    validate_raster,
)
from .reproject import get_utm_epsg, reproject_raster
from .resample import resample_raster
from .thumbnail import generate_thumbnail
from .tiles import generate_tiles

__all__ = [
    "open_raster",
    "read_metadata",
    "get_raster_info",
    "calculate_statistics",
    "calculate_histogram",
    "validate_raster",
    "save_metadata_to_db",
    "build_overviews",
    "has_overviews",
    "get_overview_levels",
    "generate_tiles",
    "reproject_raster",
    "get_utm_epsg",
    "resample_raster",
    "crop_raster",
    "clip_raster_with_polygon",
    "clip_raster_with_aoi",
    "clip_raster_with_rectangle",
    "mosaic_rasters",
    "extract_bands",
    "select_single_band",
    "set_nodata",
    "fill_nodata",
    "generate_thumbnail",
]
