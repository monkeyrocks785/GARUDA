"""Configuration for the Temporal Comparison Engine."""

# Supported raster formats for comparison
SUPPORTED_FORMATS = {
    ".tif": "GeoTIFF",
    ".tiff": "TIFF",
    ".geotiff": "GeoTIFF",
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
}

SUPPORTED_EXTENSIONS = set(SUPPORTED_FORMATS.keys())

# Comparison modes
COMPARISON_MODES = {
    "side_by_side": "Side-by-Side Comparison",
    "swipe": "Swipe Comparison",
    "overlay": "Overlay Comparison",
    "opacity": "Opacity Comparison",
    "blink": "Blink Comparison",
    "difference": "Difference Layer Preview",
}

DEFAULT_COMPARISON_MODE = "side_by_side"

# Difference visualization types
DIFFERENCE_TYPES = {
    "absolute": "Absolute Pixel Difference",
    "thresholded": "Thresholded Difference",
    "false_color": "False-Color Difference Map",
    "histogram": "Histogram Comparison",
}

DEFAULT_DIFFERENCE_TYPE = "absolute"

# Threshold for difference visualization (0-255 scale mapped to 0-1)
DEFAULT_DIFFERENCE_THRESHOLD = 0.1

# Synchronization options
SYNC_OPTIONS = {
    "pan": "Pan Synchronization",
    "zoom": "Zoom Synchronization",
    "rotation": "Rotation Synchronization",
    "cursor": "Cursor Position Synchronization",
    "aoi": "Selected AOI Synchronization",
    "visibility": "Layer Visibility Synchronization",
}

DEFAULT_SYNC_OPTIONS = ["pan", "zoom", "cursor"]

# Timeline / playback
DEFAULT_PLAYBACK_SPEED = 1.0
MIN_PLAYBACK_SPEED = 0.25
MAX_PLAYBACK_SPEED = 4.0
PLAYBACK_SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0]

# Session statuses
SESSION_STATUSES = {
    "active": "Active",
    "archived": "Archived",
    "deleted": "Deleted",
}

# Export formats
EXPORT_FORMATS = {
    "png": "PNG Image",
    "tiff": "GeoTIFF",
    "pdf": "PDF Report",
    "json": "JSON Data",
}

# Export scope
EXPORT_SCOPES = {
    "current_view": "Current View",
    "all_views": "All Views",
    "side_by_side": "Side-by-Side Composite",
    "difference": "Difference Layer",
}

# Measurement units
MEASUREMENT_UNITS = {
    "pixels": "Pixels",
    "meters": "Meters",
    "degrees": "Degrees",
}

DEFAULT_MEASUREMENT_UNIT = "pixels"

# Annotation defaults
ANNOTATION_COLORS = [
    "#FF0000", "#00FF00", "#0000FF", "#FFFF00",
    "#FF00FF", "#00FFFF", "#FF8000", "#8000FF",
]

DEFAULT_ANNOTATION_COLOR = "#FF0000"

# Annotation shapes
ANNOTATION_SHAPES = {
    "point": "Point",
    "line": "Line",
    "polygon": "Polygon",
    "rectangle": "Rectangle",
    "circle": "Circle",
    "text": "Text Note",
}

# Storage subdirectories
SESSIONS_DIR = "comparison_sessions"
EXPORTS_DIR = "comparison_exports"
SCREENSHOTS_DIR = "screenshots"
