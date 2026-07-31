"""Configuration for the Image Registration Engine."""

# Supported raster formats
SUPPORTED_FORMATS = {
    ".tif": "GeoTIFF",
    ".tiff": "GeoTIFF",
    ".geotiff": "GeoTIFF",
    ".jp2": "JPEG2000",
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
}

SUPPORTED_EXTENSIONS = set(SUPPORTED_FORMATS.keys())

# Feature detectors
FEATURE_DETECTORS = {
    "orb": "ORB (Oriented FAST and Rotated BRIEF)",
    "akaze": "AKAZE (Accelerated KAZE)",
    "brisk": "BRISK (Binary Robust Invariant Scalable Keypoints)",
    "sift": "SIFT (Scale-Invariant Feature Transform)",
}

DEFAULT_FEATURE_DETECTOR = "orb"

# Feature matcher
FEATURE_MATCHERS = {
    "bf": "Brute Force",
    "flann": "FLANN Based",
}

DEFAULT_FEATURE_MATCHER = "bf"

# Transform types
TRANSFORM_TYPES = {
    "translation": "Translation (2 DOF)",
    "rotation": "Rotation (3 DOF)",
    "scale": "Scaling (3 DOF)",
    "affine": "Affine (6 DOF)",
    "perspective": "Perspective (8 DOF)",
}

DEFAULT_TRANSFORM_TYPE = "affine"

# Resampling methods
RESAMPLING_METHODS = {
    "nearest": "Nearest Neighbor",
    "bilinear": "Bilinear Interpolation",
    "cubic": "Cubic Interpolation",
}

DEFAULT_RESAMPLING = "bilinear"

# Registration modes
REGISTRATION_MODES = {
    "automatic": "Automatic Feature-Based",
    "manual": "Manual Control Point",
    "hybrid": "Hybrid (Feature + Manual refinement)",
}

DEFAULT_REGISTRATION_MODE = "automatic"

# Registration statuses
REGISTRATION_STATUSES = {
    "pending": "Pending",
    "running": "Running",
    "completed": "Completed",
    "failed": "Failed",
    "cancelled": "Cancelled",
}

# Quality thresholds
MIN_MATCHED_POINTS = 4
MIN_INLIER_RATIO = 0.5
MAX_RMSE_PIXELS = 5.0

# Control point constraints
MAX_CONTROL_POINTS = 500
MIN_CONTROL_POINTS_AFFINE = 3
MIN_CONTROL_POINTS_PERSPECTIVE = 4

# Storage subdirectories
REGISTRATIONS_DIR = "registrations"
CONTROL_POINTS_DIR = "control_points"
RESULTS_DIR = "results"
