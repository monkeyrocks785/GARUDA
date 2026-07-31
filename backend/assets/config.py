"""Asset Library configuration constants."""


# Asset types
ASSET_TYPES = [
    "raster",
    "vector",
    "terrain",
    "document",
    "spreadsheet",
    "video",
    "audio",
    "image",
    "report",
    "model",
    "configuration",
    "log",
    "pipeline_result",
    "temporary",
    "other",
]

# Asset categories
ASSET_CATEGORIES = [
    "satellite",
    "drone",
    "survey",
    "analysis",
    "report",
    "model",
    "configuration",
    "data",
    "output",
    "archive",
    "system",
]

# Asset status options
ASSET_STATUS = [
    "active",
    "processing",
    "archived",
    "hidden",
    "deleted",
]

# Relationship types
RELATIONSHIP_TYPES = [
    "used_by",
    "produced_by",
    "derived_from",
    "related_to",
    "contains",
    "part_of",
    "version_of",
]

# Audit action types
AUDIT_ACTIONS = [
    "created",
    "imported",
    "opened",
    "modified",
    "deleted",
    "exported",
    "viewed",
    "favorited",
    "unfavorited",
    "archived",
    "restored",
    "renamed",
    "moved",
]

# Extension to asset type mapping
EXTENSION_TYPE_MAP = {
    ".tif": "raster", ".tiff": "raster", ".geotiff": "raster",
    ".jp2": "raster", ".j2k": "raster",
    ".dem": "terrain", ".dted": "terrain", ".dt0": "terrain",
    ".shp": "vector", ".geojson": "vector", ".gpkg": "vector",
    ".kml": "vector", ".kmz": "vector",
    ".pdf": "document", ".doc": "document", ".docx": "document",
    ".txt": "document", ".md": "document",
    ".csv": "spreadsheet", ".xlsx": "spreadsheet", ".xls": "spreadsheet",
    ".mp4": "video", ".avi": "video", ".mov": "video", ".mkv": "video",
    ".mp3": "audio", ".wav": "audio", ".flac": "audio",
    ".png": "image", ".jpg": "image", ".jpeg": "image",
    ".gif": "image", ".bmp": "image", ".svg": "image",
    ".json": "configuration", ".yaml": "configuration", ".yml": "configuration",
    ".xml": "configuration", ".toml": "configuration",
    ".log": "log",
    ".py": "model", ".pkl": "model", ".h5": "model", ".pt": "model",
    ".las": "raster", ".laz": "raster",
}

# Storage paths
ASSETS_DIR = "assets"
THUMBNAILS_DIR = "thumbnails"
PREVIEWS_DIR = "previews"
