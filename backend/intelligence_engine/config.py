"""Configuration constants for the Intelligence Analysis Engine."""

from pathlib import Path

from config.settings import settings, BASE_DIR

# ── Storage Paths ────────────────────────────────────────────────────────────
INTELLIGENCE_DIR = Path(settings.STORAGE_DIR) / "intelligence"
MODELS_STORAGE_DIR = Path(settings.MODELS_DIR)
RESULTS_DIR = INTELLIGENCE_DIR / "results"
TILES_DIR = INTELLIGENCE_DIR / "tiles"
PLUGINS_DIR = BASE_DIR / "intelligence_engine" / "detectors"

# ── Task Types ───────────────────────────────────────────────────────────────
TASK_TYPES = [
    "detection",
    "segmentation",
    "classification",
    "similarity_search",
    "feature_extraction",
    "ocr",
    "tracking",
]

# ── Model Status ─────────────────────────────────────────────────────────────
MODEL_STATUS = ["registered", "loading", "ready", "error", "unloaded"]

# ── Job Status ───────────────────────────────────────────────────────────────
JOB_STATUS = ["pending", "running", "paused", "completed", "failed", "cancelled"]

# ── Detection Review Status ──────────────────────────────────────────────────
REVIEW_STATUS = ["pending", "accepted", "rejected", "uncertain"]

# ── Detection Status ─────────────────────────────────────────────────────────
DETECTION_STATUS = ["active", "reviewed", "archived"]

# ── Supported Input Formats ──────────────────────────────────────────────────
SUPPORTED_RASTER_EXTENSIONS = [".tif", ".tiff", ".png", ".jpg", ".jpeg", ".jp2"]

# ── Inference Defaults ───────────────────────────────────────────────────────
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
DEFAULT_IOU_THRESHOLD = 0.45
DEFAULT_MAX_DETECTIONS = 1000
DEFAULT_TILE_SIZE = 512
DEFAULT_TILE_OVERLAP = 64
DEFAULT_BATCH_SIZE = 8

# ── Device Types ─────────────────────────────────────────────────────────────
DEVICE_TYPES = ["cpu", "cuda", "mps"]

# ── Export Formats ───────────────────────────────────────────────────────────
EXPORT_FORMATS = ["geojson", "json", "csv", "shapefile"]

# ── Infrastructure Classes ───────────────────────────────────────────────────
INFRASTRUCTURE_CLASSES = {
    0: "road",
    1: "building",
    2: "bridge",
    3: "railway",
    4: "tunnel",
    5: "port",
    6: "dam",
    7: "airport",
}

# ── Allowed Frameworks ───────────────────────────────────────────────────────
ALLOWED_FRAMEWORKS = [
    "pytorch",
    "onnx",
    "tensorflow",
    "tflite",
    "custom",
]

# ── Plugin Interface Version ─────────────────────────────────────────────────
PLUGIN_INTERFACE_VERSION = "1.0.0"
