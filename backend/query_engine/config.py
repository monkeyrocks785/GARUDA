"""Configuration constants for the Intelligence Query Engine."""

# ── Spatial Operators ────────────────────────────────────────────────────────
SPATIAL_OPERATORS = [
    "within_aoi",
    "intersects",
    "touches",
    "contains",
    "distance",
    "buffer",
    "nearest",
    "bbox",
]

# ── Temporal Operators ───────────────────────────────────────────────────────
TEMPORAL_OPERATORS = [
    "before",
    "after",
    "between",
    "first_seen",
    "last_seen",
    "observation_count",
    "duration",
]

# ── Entity Types (mirrors knowledge_engine) ──────────────────────────────────
ENTITY_TYPES = [
    "road",
    "bridge",
    "building",
    "settlement",
    "river",
    "vegetation",
    "airfield",
    "tunnel",
    "railway",
    "port",
    "unknown",
]

# ── Relationship Types (mirrors knowledge_engine) ────────────────────────────
RELATIONSHIP_TYPES = [
    "connected_to",
    "crosses",
    "adjacent_to",
    "contains",
    "part_of",
    "serves",
    "associated_with",
    "located_within_aoi",
    "appears_in_mission",
    "referenced_by_report",
    "produced_by_pipeline",
]

# ── Event Types (mirrors knowledge_engine) ───────────────────────────────────
EVENT_TYPES = [
    "created",
    "observed",
    "expanded",
    "modified",
    "connected",
    "removed",
    "merged",
    "split",
    "renamed",
    "archived",
    "analyst_corrected",
]

# ── Review Statuses ──────────────────────────────────────────────────────────
REVIEW_STATUSES = [
    "pending",
    "accepted",
    "rejected",
    "uncertain",
]

# ── Classification Levels ────────────────────────────────────────────────────
CLASSIFICATION_LEVELS = [
    "unclassified",
    "restricted",
    "confidential",
    "secret",
    "top_secret",
]

# ── Export Formats ───────────────────────────────────────────────────────────
EXPORT_FORMATS = [
    "csv",
    "geojson",
    "kml",
    "pdf",
]

# ── Query Result View Modes ──────────────────────────────────────────────────
RESULT_VIEW_MODES = [
    "table",
    "map",
    "timeline",
    "statistics",
    "details",
]

# ── Sort Directions ──────────────────────────────────────────────────────────
SORT_DIRECTIONS = [
    "asc",
    "desc",
]

# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
DEFAULT_MAX_RESULTS = 1000
QUERY_CACHE_TTL_SECONDS = 300
MAX_SAVED_QUERIES_PER_PROJECT = 100
MAX_HISTORY_ENTRIES = 1000
