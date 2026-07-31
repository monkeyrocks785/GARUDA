"""Metric Calculation Service.

Computes measurable metrics (length, area, count, etc.)
from historical entity observations stored in the Knowledge Engine.
"""

import json
import logging
import math
import time
from datetime import datetime
from typing import Any

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from growth_engine.config import ENTITY_METRICS, METRIC_UNITS
from growth_engine.database.models import GrowthHistory, GrowthMetric
from knowledge_engine.database.models import Entity, EntityObservation

logger = logging.getLogger("garuda.growth.metrics")


class MetricService:
    """Computes growth metrics from entity observations."""

    @staticmethod
    def _parse_attributes(attributes_json: str | None) -> dict:
        if not attributes_json:
            return {}
        try:
            return json.loads(attributes_json) if isinstance(attributes_json, str) else attributes_json
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def _extract_metric_from_attributes(attrs: dict, metric_name: str) -> float | None:
        key_map = {
            "length": ["length", "length_m", "road_length"],
            "area": ["area", "area_sqm", "building_area", "settlement_area"],
            "perimeter": ["perimeter", "perimeter_m"],
            "count": ["count", "building_count", "structure_count"],
            "coverage": ["coverage", "coverage_pct", "coverage_percent"],
            "density": ["density", "density_pct", "density_percent"],
            "expansion_rate": ["expansion_rate", "expansion_pct"],
            "reduction_rate": ["reduction_rate", "reduction_pct"],
            "construction_rate": ["construction_rate", "construction_pct"],
            "width": ["width", "width_m", "river_width"],
        }
        keys = key_map.get(metric_name, [metric_name])
        for k in keys:
            val = attrs.get(k)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    continue
        return None

    @staticmethod
    def compute_entity_metrics(
        db: Session,
        entity_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        start = time.monotonic()
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise ValueError(f"Entity not found: {entity_id}")

        observations = (
            db.query(EntityObservation)
            .filter(EntityObservation.entity_id == entity_id)
            .order_by(EntityObservation.observed_at.asc())
            .all()
        )

        applicable_metrics = ENTITY_METRICS.get(entity.entity_type, ["count", "observation_frequency", "confidence_trend"])
        results: list[dict] = []
        computed_values: dict[str, list[tuple[datetime | None, float]]] = {}

        for obs in observations:
            attrs = MetricService._parse_attributes(obs.attributes_json)
            for metric in applicable_metrics:
                val = MetricService._extract_metric_from_attributes(attrs, metric)
                if val is not None:
                    if metric not in computed_values:
                        computed_values[metric] = []
                    computed_values[metric].append((obs.observed_at, val))

                    unit = METRIC_UNITS.get(metric, "count")
                    gm = GrowthMetric(
                        project_id=project_id,
                        entity_id=entity_id,
                        entity_type=entity.entity_type,
                        metric_name=metric,
                        metric_value=val,
                        unit=unit,
                        confidence=obs.confidence,
                        observation_id=obs.id,
                        observation_date=obs.observed_at,
                        attributes_json=obs.attributes_json,
                    )
                    db.add(gm)
                    results.append(gm.to_dict())

        db.commit()

        elapsed = (time.monotonic() - start) * 1000
        logger.info(f"Computed {len(results)} metrics for entity {entity_id} in {elapsed:.0f}ms")

        return {
            "entity_id": entity_id,
            "entity_type": entity.entity_type,
            "entity_name": entity.name,
            "metrics_computed": len(results),
            "metric_summary": {
                metric: {
                    "values": len(vals),
                    "first": vals[0][1] if vals else None,
                    "latest": vals[-1][1] if vals else None,
                }
                for metric, vals in computed_values.items()
            },
            "execution_time_ms": round(elapsed, 2),
        }

    @staticmethod
    def compute_project_metrics(
        db: Session,
        project_id: str,
    ) -> dict[str, Any]:
        start = time.monotonic()
        entities = db.query(Entity).filter(
            Entity.project_id == project_id,
            Entity.archived == False,
        ).all()

        total_metrics = 0
        entity_results = []
        for entity in entities:
            try:
                result = MetricService.compute_entity_metrics(db, entity.id, project_id)
                entity_results.append(result)
                total_metrics += result["metrics_computed"]
            except Exception as e:
                logger.warning(f"Failed to compute metrics for entity {entity.id}: {e}")

        elapsed = (time.monotonic() - start) * 1000

        gh = GrowthHistory(
            project_id=project_id,
            calculation_type="metric_calculation",
            parameters_json=json.dumps({"entity_count": len(entities)}),
            result_summary_json=json.dumps({"total_metrics": total_metrics, "entities_processed": len(entity_results)}),
            result_count=total_metrics,
            execution_time_ms=round(elapsed, 2),
        )
        db.add(gh)
        db.commit()

        logger.info(f"Computed {total_metrics} metrics for {len(entity_results)} entities in project {project_id}")

        return {
            "project_id": project_id,
            "entities_processed": len(entity_results),
            "total_entities": len(entities),
            "total_metrics": total_metrics,
            "entity_results": entity_results,
            "execution_time_ms": round(elapsed, 2),
        }

    @staticmethod
    def get_entity_metrics(
        db: Session,
        entity_id: str,
        metric_name: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        q = db.query(GrowthMetric).filter(GrowthMetric.entity_id == entity_id)
        if metric_name:
            q = q.filter(GrowthMetric.metric_name == metric_name)
        q = q.order_by(GrowthMetric.observation_date.asc()).limit(limit)
        return [m.to_dict() for m in q.all()]

    @staticmethod
    def get_project_metrics(
        db: Session,
        project_id: str,
        entity_type: str | None = None,
        metric_name: str | None = None,
        page: int = 0,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        q = db.query(GrowthMetric).filter(GrowthMetric.project_id == project_id)
        if entity_type:
            q = q.filter(GrowthMetric.entity_type == entity_type)
        if metric_name:
            q = q.filter(GrowthMetric.metric_name == metric_name)
        total = q.count()
        items = q.order_by(GrowthMetric.observation_date.desc()).offset(page * page_size).limit(page_size).all()
        return [m.to_dict() for m in items], total

    @staticmethod
    def compute_growth_rate(
        db: Session,
        entity_id: str,
        metric_name: str,
    ) -> dict[str, Any] | None:
        metrics = (
            db.query(GrowthMetric)
            .filter(
                GrowthMetric.entity_id == entity_id,
                GrowthMetric.metric_name == metric_name,
            )
            .order_by(GrowthMetric.observation_date.asc())
            .all()
        )
        if len(metrics) < 2:
            return None

        values = [(m.observation_date, m.metric_value) for m in metrics if m.observation_date]

        first_val = values[0][1]
        last_val = values[-1][1]
        first_date = values[0][0]
        last_date = values[-1][0]

        if first_val == 0:
            return None

        days = (last_date - first_date).days if first_date and last_date else 1
        years = max(days / 365.25, 1 / 365.25)

        total_change = last_val - first_val
        annual_rate = ((last_val / first_val) ** (1 / years) - 1) * 100 if first_val > 0 else 0
        monthly_rate = ((last_val / first_val) ** (1 / (years * 12)) - 1) * 100 if first_val > 0 else 0

        changes = []
        for i in range(1, len(values)):
            if values[i - 1][1] > 0:
                pct = ((values[i][1] - values[i - 1][1]) / values[i - 1][1]) * 100
                changes.append(pct)

        avg_growth = sum(changes) / len(changes) if changes else 0
        max_growth = max(changes) if changes else 0
        min_growth = min(changes) if changes else 0

        accelerations = []
        for i in range(2, len(changes)):
            accelerations.append(changes[i] - changes[i - 1])
        acceleration = sum(accelerations) / len(accelerations) if accelerations else 0
        deceleration = -acceleration if acceleration < 0 else 0
        acceleration = acceleration if acceleration > 0 else 0

        return {
            "entity_id": entity_id,
            "metric_name": metric_name,
            "first_value": first_val,
            "latest_value": last_val,
            "total_change": total_change,
            "annual_growth": round(annual_rate, 4),
            "monthly_growth": round(monthly_rate, 4),
            "average_growth": round(avg_growth, 4),
            "maximum_growth": round(max_growth, 4),
            "minimum_growth": round(min_growth, 4),
            "acceleration": round(acceleration, 4),
            "deceleration": round(deceleration, 4),
            "observation_count": len(values),
            "days_span": days,
        }

    @staticmethod
    def compute_observation_frequency(
        db: Session,
        entity_id: str,
    ) -> dict[str, Any]:
        obs = (
            db.query(EntityObservation)
            .filter(EntityObservation.entity_id == entity_id)
            .order_by(EntityObservation.observed_at.asc())
            .all()
        )
        if len(obs) < 2:
            return {"entity_id": entity_id, "observation_frequency": 0, "total_observations": len(obs)}

        first_date = obs[0].observed_at
        last_date = obs[-1].observed_at
        days = (last_date - first_date).days if first_date and last_date else 1
        years = max(days / 365.25, 1 / 365.25)
        freq = len(obs) / years

        return {
            "entity_id": entity_id,
            "observation_frequency": round(freq, 4),
            "total_observations": len(obs),
            "first_observation": first_date.isoformat() if first_date else None,
            "latest_observation": last_date.isoformat() if last_date else None,
            "days_span": days,
        }

    @staticmethod
    def compute_confidence_trend(
        db: Session,
        entity_id: str,
    ) -> dict[str, Any]:
        obs = (
            db.query(EntityObservation)
            .filter(EntityObservation.entity_id == entity_id)
            .order_by(EntityObservation.observed_at.asc())
            .all()
        )
        if len(obs) < 2:
            return {"entity_id": entity_id, "confidence_trend": 0, "average_confidence": 0}

        confidences = [o.confidence for o in obs if o.observed_at]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        first_half = confidences[:len(confidences)//2]
        second_half = confidences[len(confidences)//2:]
        trend = (sum(second_half) / len(second_half) - sum(first_half) / len(first_half)) if first_half and second_half else 0

        return {
            "entity_id": entity_id,
            "confidence_trend": round(trend, 4),
            "average_confidence": round(avg_conf, 4),
            "first_confidence": confidences[0] if confidences else 0,
            "latest_confidence": confidences[-1] if confidences else 0,
        }
