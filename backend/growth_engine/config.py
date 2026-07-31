"""Configuration constants for the Growth Analytics Engine."""

ENTITY_TYPES = [
    "road", "bridge", "building", "settlement", "river",
    "vegetation", "airfield", "tunnel", "railway", "port", "airport", "unknown",
]

METRICS = [
    "length", "area", "perimeter", "count", "coverage", "density",
    "expansion_rate", "reduction_rate", "construction_rate",
    "annual_growth", "monthly_growth", "average_growth",
    "maximum_growth", "minimum_growth",
    "acceleration", "deceleration",
    "observation_frequency", "confidence_trend",
]

ENTITY_METRICS = {
    "road": ["length", "coverage", "density", "expansion_rate", "construction_rate",
             "annual_growth", "monthly_growth", "average_growth", "maximum_growth",
             "minimum_growth", "observation_frequency", "confidence_trend"],
    "bridge": ["count", "construction_rate", "annual_growth", "monthly_growth",
               "average_growth", "observation_frequency", "confidence_trend"],
    "building": ["count", "area", "coverage", "density", "construction_rate",
                 "annual_growth", "monthly_growth", "average_growth", "maximum_growth",
                 "minimum_growth", "observation_frequency", "confidence_trend"],
    "settlement": ["area", "coverage", "density", "expansion_rate",
                   "annual_growth", "monthly_growth", "average_growth", "maximum_growth",
                   "minimum_growth", "acceleration", "deceleration",
                   "observation_frequency", "confidence_trend"],
    "river": ["length", "coverage", "reduction_rate",
              "annual_growth", "monthly_growth", "average_growth",
              "observation_frequency", "confidence_trend"],
    "vegetation": ["area", "coverage", "density", "reduction_rate",
                   "annual_growth", "monthly_growth", "average_growth",
                   "acceleration", "deceleration",
                   "observation_frequency", "confidence_trend"],
    "airfield": ["count", "area", "coverage",
                 "observation_frequency", "confidence_trend"],
    "tunnel": ["count", "length", "construction_rate",
               "annual_growth", "observation_frequency", "confidence_trend"],
    "railway": ["length", "coverage", "density",
                "annual_growth", "observation_frequency", "confidence_trend"],
    "port": ["count", "area", "expansion_rate",
             "annual_growth", "observation_frequency", "confidence_trend"],
    "airport": ["count", "area", "construction_rate",
                "annual_growth", "observation_frequency", "confidence_trend"],
    "unknown": ["count", "observation_frequency", "confidence_trend"],
}

CHANGE_STATISTICS = [
    "road_added", "buildings_added", "river_width_change",
    "forest_loss", "settlement_expansion", "bridge_construction",
]

FORECAST_ALGORITHMS = [
    "linear_regression",
    "moving_average",
    "polynomial_regression",
    "exponential_trend",
]

DEFAULT_FORECAST_STEPS = 12
DEFAULT_CONFIDENCE_LEVEL = 0.95
MIN_HISTORY_POINTS = 3

METRIC_UNITS = {
    "length": "meters",
    "area": "sq_meters",
    "perimeter": "meters",
    "count": "count",
    "coverage": "percent",
    "density": "percent",
    "expansion_rate": "percent",
    "reduction_rate": "percent",
    "construction_rate": "percent",
    "annual_growth": "percent",
    "monthly_growth": "percent",
    "average_growth": "percent",
    "maximum_growth": "percent",
    "minimum_growth": "percent",
    "acceleration": "percent_per_year",
    "deceleration": "percent_per_year",
    "observation_frequency": "observations_per_year",
    "confidence_trend": "score",
}

HOTSPOT_DEFAULT_THRESHOLD = 2.0
MAX_HOTSPOT_RESULTS = 50
