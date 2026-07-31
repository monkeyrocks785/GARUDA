"""Growth Analytics Engine - Package Init.

Calculates measurable trends, growth metrics, and forecasts
from historical observations stored in the Knowledge Engine.
"""

from growth_engine.services.metric_service import MetricService
from growth_engine.services.temporal_service import TemporalAnalysisService
from growth_engine.services.forecast_service import ForecastService
from growth_engine.services.hotspot_service import HotspotService
from growth_engine.services.change_statistics_service import ChangeStatisticsService

__all__ = [
    "MetricService",
    "TemporalAnalysisService",
    "ForecastService",
    "HotspotService",
    "ChangeStatisticsService",
]
