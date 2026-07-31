"""Configuration constants for the Knowledge Engine."""

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

ENTITY_STATUSES = [
    "active",
    "inactive",
    "archived",
    "deleted",
]

OBSERVATION_TYPES = [
    "detection",
    "measurement",
    "analyst_note",
    "imported",
    "derived",
]

CHANGE_TYPES = [
    "created",
    "updated",
    "attribute_changed",
    "geometry_changed",
    "status_changed",
    "observation_added",
    "event_added",
    "relationship_added",
    "relationship_removed",
    "analyst_note",
    "merged",
    "split",
]

DEFAULT_CONFIDENCE = 1.0
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
