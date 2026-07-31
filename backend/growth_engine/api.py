"""Growth Analytics Engine API.

Provides endpoints for growth metric calculation, forecasting,
trend analysis, hotspot detection, and change statistics.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from growth_engine.config import (
    CHANGE_STATISTICS,
    ENTITY_METRICS,
    ENTITY_TYPES,
    FORECAST_ALGORITHMS,
    METRICS,
    METRIC_UNITS,
)
from growth_engine.database.models import GrowthHistory
from growth_engine.services.change_statistics_service import ChangeStatisticsService
from growth_engine.services.forecast_service import ForecastService
from growth_engine.services.hotspot_service import HotspotService
from growth_engine.services.metric_service import MetricService
from growth_engine.services.temporal_service import TemporalAnalysisService

logger = logging.getLogger("garuda.growth.api")

router = APIRouter(prefix="/growth", tags=["Growth Analytics Engine"])


class CalculateMetricsRequest(BaseModel):
    project_id: str
    entity_id: str | None = None


class ForecastRequest(BaseModel):
    project_id: str
    entity_id: str
    metric_name: str = "count"
    algorithm: str = "linear_regression"
    steps: int = 12
    confidence_level: float = 0.95
    algorithm_params: dict | None = None
    step_unit: str = "months"


class HotspotRequest(BaseModel):
    project_id: str
    metric_name: str = "count"
    threshold: float = 2.0
    entity_type: str | None = None


@router.get("/config")
def get_growth_config():
    """Get Growth Analytics Engine configuration."""
    return {
        "entity_types": ENTITY_TYPES,
        "metrics": METRICS,
        "entity_metrics": ENTITY_METRICS,
        "metric_units": METRIC_UNITS,
        "forecast_algorithms": FORECAST_ALGORITHMS,
        "change_statistics": CHANGE_STATISTICS,
    }


@router.post("/calculate")
def calculate_metrics(
    req: CalculateMetricsRequest,
    db: Session = Depends(get_db),
):
    """Calculate growth metrics for an entity or entire project."""
    try:
        if req.entity_id:
            result = MetricService.compute_entity_metrics(db, req.entity_id, req.project_id)
        else:
            result = MetricService.compute_project_metrics(db, req.project_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Metric calculation failed")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/metrics")
def get_metrics(
    project_id: str = Query(...),
    entity_id: str | None = Query(None),
    entity_type: str | None = Query(None),
    metric_name: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve computed growth metrics."""
    if entity_id:
        items = MetricService.get_entity_metrics(db, entity_id, metric_name)
        return {"items": items, "total": len(items), "page": 0, "page_size": len(items)}
    items, total = MetricService.get_project_metrics(db, project_id, entity_type, metric_name, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/metrics/growth-rate")
def get_growth_rate(
    entity_id: str = Query(...),
    metric_name: str = Query("count"),
    db: Session = Depends(get_db),
):
    """Compute growth rate for a specific entity metric."""
    result = MetricService.compute_growth_rate(db, entity_id, metric_name)
    if result is None:
        raise HTTPException(status_code=404, detail="Insufficient data for growth rate calculation")
    return result


@router.get("/metrics/observation-frequency")
def get_observation_frequency(
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Compute observation frequency for an entity."""
    return MetricService.compute_observation_frequency(db, entity_id)


@router.get("/metrics/confidence-trend")
def get_confidence_trend(
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Compute confidence trend for an entity."""
    return MetricService.compute_confidence_trend(db, entity_id)


@router.get("/timeline")
def get_timeline(
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Get complete entity timeline with observations, events, and metrics."""
    try:
        return TemporalAnalysisService.get_entity_timeline(db, entity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/timeline/growth")
def get_growth_timeline(
    entity_id: str = Query(...),
    metric_name: str = Query("count"),
    db: Session = Depends(get_db),
):
    """Get growth timeline for a specific metric."""
    return TemporalAnalysisService.get_growth_timeline(db, entity_id, metric_name)


@router.get("/timeline/expansion")
def get_expansion_timeline(
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Get expansion timeline (area-based)."""
    try:
        return TemporalAnalysisService.get_expansion_timeline(db, entity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/timeline/reduction")
def get_reduction_timeline(
    entity_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Get reduction timeline (area-based)."""
    try:
        return TemporalAnalysisService.get_reduction_timeline(db, entity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/historical")
def get_historical_timeline(
    project_id: str = Query(...),
    entity_type: str | None = Query(None),
    metric_name: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get aggregated historical timeline for a project."""
    return TemporalAnalysisService.get_historical_timeline(db, project_id, entity_type, metric_name)


@router.post("/forecast")
def generate_forecast(
    req: ForecastRequest,
    db: Session = Depends(get_db),
):
    """Generate a forecast for an entity metric."""
    try:
        result = ForecastService.generate_forecast(
            db,
            project_id=req.project_id,
            entity_id=req.entity_id,
            metric_name=req.metric_name,
            algorithm=req.algorithm,
            steps=req.steps,
            confidence_level=req.confidence_level,
            algorithm_params=req.algorithm_params,
            step_unit=req.step_unit,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Forecast generation failed")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/forecast")
def get_forecasts(
    project_id: str = Query(...),
    entity_id: str | None = Query(None),
    entity_type: str | None = Query(None),
    metric_name: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve forecast results."""
    if entity_id:
        items = ForecastService.get_entity_forecasts(db, entity_id)
        return {"items": items, "total": len(items), "page": 0, "page_size": len(items)}
    items, total = ForecastService.get_project_forecasts(db, project_id, entity_type, metric_name, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/forecast/models")
def get_forecast_models(
    project_id: str = Query(...),
    entity_id: str | None = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Retrieve forecast model configurations."""
    return {"items": ForecastService.get_forecast_models(db, project_id, entity_id, active_only)}


@router.post("/hotspots")
def detect_hotspots(
    req: HotspotRequest,
    db: Session = Depends(get_db),
):
    """Detect growth hotspots in a project."""
    try:
        result = HotspotService.detect_hotspots(
            db,
            project_id=req.project_id,
            metric_name=req.metric_name,
            threshold=req.threshold,
            entity_type=req.entity_type,
        )
        return result
    except Exception as e:
        logger.exception("Hotspot detection failed")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/change-statistics")
def calculate_change_statistics(
    project_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Calculate change statistics for a project."""
    try:
        return ChangeStatisticsService.calculate_change_statistics(db, project_id)
    except Exception as e:
        logger.exception("Change statistics calculation failed")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/change-statistics")
def get_change_statistics_history(
    project_id: str = Query(...),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get change statistics calculation history."""
    items, total = ChangeStatisticsService.get_change_statistics_history(db, project_id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/history")
def get_growth_history(
    project_id: str = Query(...),
    calculation_type: str | None = Query(None),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get growth calculation history."""
    q = db.query(GrowthHistory).filter(GrowthHistory.project_id == project_id)
    if calculation_type:
        q = q.filter(GrowthHistory.calculation_type == calculation_type)
    total = q.count()
    items = q.order_by(GrowthHistory.executed_at.desc()).offset(page * page_size).limit(page_size).all()
    return {
        "items": [h.to_dict() for h in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
