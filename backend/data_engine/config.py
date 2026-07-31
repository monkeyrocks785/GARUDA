"""Data Engine configuration constants."""


# Supported file extensions by category
RASTER_EXTENSIONS = {
    ".tif", ".tiff", ".geotiff", ".gtiff",
    ".jp2", ".j2k", ".jpeg2000",
    ".png", ".jpg", ".jpeg",
    ".dem", ".dted", ".dt0", ".dt1", ".dt2",
    ".img", ".bmp", ".gif",
}

VECTOR_EXTENSIONS = {
    ".geojson", ".json",
    ".shp", ".shx", ".dbf", ".prj", ".cpg",
    ".gpkg", ".geopackage",
    ".kml", ".kmz",
}

TABULAR_EXTENSIONS = {
    ".csv", ".tsv", ".txt",
}

LASER_EXTENSIONS = {
    ".las", ".laz",
}

ALL_EXTENSIONS = RASTER_EXTENSIONS | VECTOR_EXTENSIONS | TABULAR_EXTENSIONS | LASER_EXTENSIONS

# Extension to dataset type mapping
EXTENSION_TYPE_MAP = {
    ".tif": "raster", ".tiff": "raster", ".geotiff": "raster", ".gtiff": "raster",
    ".jp2": "raster", ".j2k": "raster", ".jpeg2000": "raster",
    ".png": "image", ".jpg": "image", ".jpeg": "image",
    ".dem": "raster", ".dted": "raster",
    ".img": "raster", ".bmp": "image", ".gif": "image",
    ".geojson": "vector", ".json": "vector",
    ".shp": "vector", ".gpkg": "vector", ".geopackage": "vector",
    ".kml": "vector", ".kmz": "vector",
    ".csv": "tabular", ".tsv": "tabular", ".txt": "tabular",
    ".las": "laser", ".laz": "laser",
}

# Dataset status options
DATASET_STATUS = [
    "importing",
    "validating",
    "indexed",
    "ready",
    "error",
    "archived",
]

# Dataset type options
DATASET_TYPES = [
    "raster",
    "vector",
    "image",
    "tabular",
    "laser",
    "video",
    "sar",
    "drone",
    "other",
]

# Storage paths
DATASETS_SUBDIR = "datasets"
THUMBNAILS_SUBDIR = "thumbnails"
METADATA_SUBDIR = "metadata"

# Import settings
MAX_IMPORT_SIZE_GB = 50
CHUNK_SIZE_MB = 10
