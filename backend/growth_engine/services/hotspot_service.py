"""Hotspot Detection Service.

Identifies AOIs or entities exhibiting unusually high growth rates
relative to their historical baselines.
"""

import json
import logging
import time
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from growth_engine.config import HOTSPOT_DEFAULT_THRESHOLD, MAX_HOTSPOT_RESULTS
from growth_engine.database.models import GrowthHistory, GrowthMetric
from growth_engine.services.metric_service import MetricService
from knowledge_engine.database.models import Entity, EntityObservation

logger = logging.getLogger("garuda.growth.hotspot")


class HotspotService:
    """Detects growth hotspots across entities in a project."""

    @staticmethod
    def detect_hotspots(
        db: Session,
        project_id: str,
        metric_name: str = "count",
        threshold: float = HOTSPOT_DEFAULT_THRESHOLD,
        entity_type: str | None = None,
    ) -> dict[str, Any]:
        start = time.monotonic()

        q = db.query(Entity).filter(
            Entity.project_id == project_id,
            Entity.archived == False,
        )
        if entity_type:
            q = q.filter(Entity.entity_type == entity_type)
        entities = q.all()

        growth_rates: list[dict] = []
        for entity in entities:
            try:
                rate = MetricService.compute_growth_rate(db, entity.id, metric_name)
                if rate and rate.get("annual_growth") is not None:
                    growth_rates.append({
                        "entity_id": entity.id,
                        "entity_name": entity.name,
                        "entity_type": entity.entity_type,
                        "annual_growth": rate["annual_growth"],
                        "monthly_growth": rate["monthly_growth"],
                        "observation_count": rate["observation_count"],
                        "days_span": rate["days_span"],
                    })
            except Exception as e:
                logger.debug(f"Could not compute growth rate for {entity.id}: {e}")

        if not growth_rates:
            return {
                "project_id": project_id,
                "metric_name": metric_name,
                "threshold": threshold,
                "hotspots": [],
                "total_entities_analyzed": len(entities),
                "entities_with_data": 0,
            }

        rates = np.array([r["annual_growth"] for r in growth_rates])
        mean_rate = float(np.mean(rates))
        std_rate = float(np.std(rates)) if np.std(rates) > 0 else 1.0

        hotspots = []
        for r in growth_rates:
            z_score = (r["annual_growth"] - mean_rate) / std_rate if std_rate > 0 else 0
            if z_score > threshold:
                hotspots.append({
                    **r,
                    "z_score": round(float(z_score), 4),
                    "above_mean_by": round(float(r["annual_growth"] - mean_rate), 4),
                })

        hotspots.sort(key=lambda h: h["z_score"], reverse=True)
        hotspots = hotspots[:MAX_HOTSPOT_RESULTS]

        elapsed = (time.monotonic() - start) * 1000

        gh = GrowthHistory(
            project_id=project_id,
            calculation_type="hotspot_detection",
            parameters_json=json.dumps({
                "metric_name": metric_name,
                "threshold": threshold,
                "entity_type": entity_type,
            }),
            result_summary_json=json.dumps({
                "hotspots_found": len(hotspots),
                "total_analyzed": len(entities),
            }),
            result_count=len(hotspots),
            execution_time_ms=round(elapsed, 2),
        )
        db.add(gh)
        db.commit()

        return {
            "project_id": project_id,
            "metric_name": metric_name,
            "threshold": threshold,
            "entity_type": entity_type,
            "total_entities_analyzed": len(entities),
            "entities_with_data": len(growth_rates),
            "mean_growth_rate": round(mean_rate, 4),
            "std_growth_rate": round(std_rate, 4),
            "hotspots": hotspots,
            "execution_time_ms": round(elapsed, 2),
        }
