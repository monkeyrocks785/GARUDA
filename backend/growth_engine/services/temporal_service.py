"""Temporal Analysis Service.

Analyzes entity timelines: first/latest observation, growth,
expansion, and reduction timelines.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from growth_engine.database.models import GrowthHistory, GrowthMetric
from knowledge_engine.database.models import Entity, EntityObservation, EntityEvent

logger = logging.getLogger("garuda.growth.temporal")


class TemporalAnalysisService:
    """Analyzes historical timelines for entities."""

    @staticmethod
    def get_entity_timeline(
        db: Session,
        entity_id: str,
    ) -> dict[str, Any]:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise ValueError(f"Entity not found: {entity_id}")

        observations = (
            db.query(EntityObservation)
            .filter(EntityObservation.entity_id == entity_id)
            .order_by(EntityObservation.observed_at.asc())
            .all()
        )

        events = (
            db.query(EntityEvent)
            .filter(EntityEvent.entity_id == entity_id)
            .order_by(EntityEvent.event_time.asc())
            .all()
        )

        metrics = (
            db.query(GrowthMetric)
            .filter(GrowthMetric.entity_id == entity_id)
            .order_by(GrowthMetric.observation_date.asc())
            .all()
        )

        timeline = {
            "entity_id": entity_id,
            "entity_type": entity.entity_type,
            "entity_name": entity.name,
            "first_observation": observations[0].observed_at.isoformat()
                if observations and observations[0].observed_at else None,
            "latest_observation": observations[-1].observed_at.isoformat()
                if observations and observations[-1].observed_at else None,
            "total_observations": len(observations),
            "total_events": len(events),
            "observations": [
                {
                    "id": o.id,
                    "observation_type": o.observation_type,
                    "observed_at": o.observed_at.isoformat() if o.observed_at else None,
                    "confidence": o.confidence,
                    "attributes_json": o.attributes_json,
                }
                for o in observations
            ],
            "events": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "event_time": e.event_time.isoformat() if e.event_time else None,
                    "description": e.description,
                }
                for e in events
            ],
            "metric_timeline": [
                {
                    "metric_name": m.metric_name,
                    "metric_value": m.metric_value,
                    "unit": m.unit,
                    "observation_date": m.observation_date.isoformat()
                        if m.observation_date else None,
                }
                for m in metrics
            ],
        }

        return timeline

    @staticmethod
    def get_growth_timeline(
        db: Session,
        entity_id: str,
        metric_name: str = "count",
    ) -> dict[str, Any]:
        metrics = (
            db.query(GrowthMetric)
            .filter(
                GrowthMetric.entity_id == entity_id,
                GrowthMetric.metric_name == metric_name,
            )
            .order_by(GrowthMetric.observation_date.asc())
            .all()
        )

        if not metrics:
            return {
                "entity_id": entity_id,
                "metric_name": metric_name,
                "data_points": [],
                "trend": None,
            }

        values = [(m.observation_date, m.metric_value) for m in metrics]

        first_val = values[0][1]
        last_val = values[-1][1]
        growth = last_val - first_val
        growth_pct = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0

        return {
            "entity_id": entity_id,
            "metric_name": metric_name,
            "data_points": [
                {
                    "date": v[0].isoformat() if v[0] else None,
                    "value": v[1],
                }
                for v in values
            ],
            "first_value": first_val,
            "latest_value": last_val,
            "absolute_growth": growth,
            "percentage_growth": round(growth_pct, 4),
            "trend": "increasing" if growth > 0 else ("decreasing" if growth < 0 else "stable"),
        }

    @staticmethod
    def get_expansion_timeline(
        db: Session,
        entity_id: str,
    ) -> dict[str, Any]:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise ValueError(f"Entity not found: {entity_id}")

        area_metrics = (
            db.query(GrowthMetric)
            .filter(
                GrowthMetric.entity_id == entity_id,
                GrowthMetric.metric_name == "area",
            )
            .order_by(GrowthMetric.observation_date.asc())
            .all()
        )

        if not area_metrics:
            return {
                "entity_id": entity_id,
                "entity_name": entity.name,
                "expansion_data": [],
                "total_expansion": None,
            }

        values = [(m.observation_date, m.metric_value) for m in area_metrics]
        first_area = values[0][1]
        last_area = values[-1][1]
        expansion = last_area - first_area
        expansion_pct = ((last_area - first_area) / first_area * 100) if first_area != 0 else 0

        return {
            "entity_id": entity_id,
            "entity_name": entity.name,
            "expansion_data": [
                {"date": v[0].isoformat() if v[0] else None, "area": v[1]} for v in values
            ],
            "first_area": first_area,
            "latest_area": last_area,
            "total_expansion": expansion,
            "percentage_expansion": round(expansion_pct, 4),
        }

    @staticmethod
    def get_reduction_timeline(
        db: Session,
        entity_id: str,
    ) -> dict[str, Any]:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise ValueError(f"Entity not found: {entity_id}")

        area_metrics = (
            db.query(GrowthMetric)
            .filter(
                GrowthMetric.entity_id == entity_id,
                GrowthMetric.metric_name == "area",
            )
            .order_by(GrowthMetric.observation_date.asc())
            .all()
        )

        if not area_metrics:
            return {
                "entity_id": entity_id,
                "entity_name": entity.name,
                "reduction_data": [],
                "total_reduction": None,
            }

        values = [(m.observation_date, m.metric_value) for m in area_metrics]
        first_area = values[0][1]
        last_area = values[-1][1]
        reduction = first_area - last_area
        reduction_pct = ((first_area - last_area) / first_area * 100) if first_area != 0 else 0

        return {
            "entity_id": entity_id,
            "entity_name": entity.name,
            "reduction_data": [
                {"date": v[0].isoformat() if v[0] else None, "area": v[1]} for v in values
            ],
            "first_area": first_area,
            "latest_area": last_area,
            "total_reduction": max(0, reduction),
            "percentage_reduction": round(max(0, reduction_pct), 4),
        }

    @staticmethod
    def get_historical_timeline(
        db: Session,
        project_id: str,
        entity_type: str | None = None,
        metric_name: str | None = None,
    ) -> dict[str, Any]:
        q = db.query(GrowthMetric).filter(GrowthMetric.project_id == project_id)
        if entity_type:
            q = q.filter(GrowthMetric.entity_type == entity_type)
        if metric_name:
            q = q.filter(GrowthMetric.metric_name == metric_name)
        q = q.order_by(GrowthMetric.observation_date.asc())

        metrics = q.all()
        if not metrics:
            return {"project_id": project_id, "data_points": [], "summary": {}}

        values_by_metric: dict[str, list[dict]] = {}
        for m in metrics:
            if m.metric_name not in values_by_metric:
                values_by_metric[m.metric_name] = []
            values_by_metric[m.metric_name].append({
                "date": m.observation_date.isoformat() if m.observation_date else None,
                "value": m.metric_value,
                "entity_id": m.entity_id,
                "entity_type": m.entity_type,
            })

        summary = {}
        for name, vals in values_by_metric.items():
            vals_sorted = sorted(vals, key=lambda x: x["date"] or "")
            first_v = vals_sorted[0]["value"] if vals_sorted else 0
            last_v = vals_sorted[-1]["value"] if vals_sorted else 0
            summary[name] = {
                "data_points": len(vals),
                "first_value": first_v,
                "latest_value": last_v,
                "min_value": min(v["value"] for v in vals),
                "max_value": max(v["value"] for v in vals),
                "average_value": sum(v["value"] for v in vals) / len(vals),
            }

        return {
            "project_id": project_id,
            "entity_type": entity_type,
            "metric_name": metric_name,
            "data_by_metric": values_by_metric,
            "summary": summary,
        }

    @staticmethod
    def record_analysis(
        db: Session,
        project_id: str,
        calculation_type: str,
        parameters: dict | None = None,
        result_summary: dict | None = None,
        result_count: int = 0,
        execution_time_ms: float = 0,
    ) -> None:
        gh = GrowthHistory(
            project_id=project_id,
            calculation_type=calculation_type,
            parameters_json=json.dumps(parameters) if parameters else None,
            result_summary_json=json.dumps(result_summary) if result_summary else None,
            result_count=result_count,
            execution_time_ms=round(execution_time_ms, 2),
        )
        db.add(gh)
        db.commit()
