"""Change Statistics Service.

Calculates specific change statistics: road added, buildings added,
river width change, forest loss, settlement expansion, bridge construction.
"""

import json
import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from growth_engine.config import CHANGE_STATISTICS
from growth_engine.database.models import GrowthHistory, GrowthMetric
from knowledge_engine.database.models import Entity, EntityObservation, EntityEvent

logger = logging.getLogger("garuda.growth.changes")


class ChangeStatisticsService:
    """Computes meaningful change statistics for analyst review."""

    @staticmethod
    def calculate_change_statistics(
        db: Session,
        project_id: str,
    ) -> dict[str, Any]:
        start = time.monotonic()

        entities = (
            db.query(Entity)
            .filter(Entity.project_id == project_id, Entity.archived == False)
            .all()
        )

        road_growth = ChangeStatisticsService._calculate_type_change(db, project_id, "road", "length")
        buildings_change = ChangeStatisticsService._calculate_type_change(db, project_id, "building", "count")
        river_width = ChangeStatisticsService._calculate_river_width_change(db, project_id)
        forest_loss = ChangeStatisticsService._calculate_forest_loss(db, project_id)
        settlement_expansion = ChangeStatisticsService._calculate_type_change(db, project_id, "settlement", "area")
        bridge_construction = ChangeStatisticsService._calculate_type_change(db, project_id, "bridge", "count")

        stats = {
            "road_added": road_growth,
            "buildings_added": buildings_change,
            "river_width_change": river_width,
            "forest_loss": forest_loss,
            "settlement_expansion": settlement_expansion,
            "bridge_construction": bridge_construction,
        }

        elapsed = (time.monotonic() - start) * 1000

        gh = GrowthHistory(
            project_id=project_id,
            calculation_type="change_statistics",
            parameters_json=json.dumps({"entity_count": len(entities)}),
            result_summary_json=json.dumps({k: v.get("change") if v else None for k, v in stats.items()}),
            result_count=len(stats),
            execution_time_ms=round(elapsed, 2),
        )
        db.add(gh)
        db.commit()

        return {
            "project_id": project_id,
            "statistics": stats,
            "execution_time_ms": round(elapsed, 2),
        }

    @staticmethod
    def _calculate_type_change(
        db: Session,
        project_id: str,
        entity_type: str,
        metric_name: str,
    ) -> dict | None:
        entities = (
            db.query(Entity)
            .filter(
                Entity.project_id == project_id,
                Entity.entity_type == entity_type,
                Entity.archived == False,
            )
            .all()
        )

        if not entities:
            return {"entity_type": entity_type, "change": 0, "entities_found": 0}

        total_before = 0
        total_after = 0
        count = 0

        for entity in entities:
            metrics = (
                db.query(GrowthMetric)
                .filter(
                    GrowthMetric.entity_id == entity.id,
                    GrowthMetric.metric_name == metric_name,
                )
                .order_by(GrowthMetric.observation_date.asc())
                .all()
            )
            if len(metrics) >= 2:
                total_before += metrics[0].metric_value
                total_after += metrics[-1].metric_value
                count += 1

        if count == 0:
            return {"entity_type": entity_type, "change": 0, "entities_found": len(entities)}

        change = total_after - total_before
        change_pct = (change / total_before * 100) if total_before != 0 else 0

        return {
            "entity_type": entity_type,
            "metric": metric_name,
            "entities_found": len(entities),
            "entities_with_data": count,
            "before_total": round(total_before, 2),
            "after_total": round(total_after, 2),
            "change": round(change, 2),
            "change_percentage": round(change_pct, 2),
        }

    @staticmethod
    def _calculate_river_width_change(db: Session, project_id: str) -> dict | None:
        rivers = (
            db.query(Entity)
            .filter(
                Entity.project_id == project_id,
                Entity.entity_type == "river",
                Entity.archived == False,
            )
            .all()
        )

        total_width_change = 0
        count = 0
        for river in rivers:
            obs = (
                db.query(EntityObservation)
                .filter(EntityObservation.entity_id == river.id)
                .order_by(EntityObservation.observed_at.asc())
                .all()
            )
            widths = []
            for o in obs:
                attrs = {}
                if o.attributes_json:
                    try:
                        attrs = json.loads(o.attributes_json)
                    except (json.JSONDecodeError, TypeError):
                        continue
                width = attrs.get("width") or attrs.get("width_m") or attrs.get("river_width")
                if width is not None:
                    widths.append((o.observed_at, float(width)))

            if len(widths) >= 2:
                total_width_change += widths[-1][1] - widths[0][1]
                count += 1

        if count == 0:
            return {"rivers_found": len(rivers), "rivers_with_data": 0, "average_width_change": 0}

        return {
            "rivers_found": len(rivers),
            "rivers_with_data": count,
            "average_width_change": round(total_width_change / count, 2),
            "total_width_change": round(total_width_change, 2),
        }

    @staticmethod
    def _calculate_forest_loss(db: Session, project_id: str) -> dict | None:
        vegetation = (
            db.query(Entity)
            .filter(
                Entity.project_id == project_id,
                Entity.entity_type == "vegetation",
                Entity.archived == False,
            )
            .all()
        )

        total_loss = 0
        count = 0
        for veg in vegetation:
            metrics = (
                db.query(GrowthMetric)
                .filter(
                    GrowthMetric.entity_id == veg.id,
                    GrowthMetric.metric_name == "area",
                )
                .order_by(GrowthMetric.observation_date.asc())
                .all()
            )
            if len(metrics) >= 2:
                loss = metrics[0].metric_value - metrics[-1].metric_value
                if loss > 0:
                    total_loss += loss
                count += 1

        if count == 0:
            return {"vegetation_patches_found": len(vegetation), "patches_with_data": 0, "total_forest_loss": 0}

        return {
            "vegetation_patches_found": len(vegetation),
            "patches_with_data": count,
            "total_forest_loss": round(max(0, total_loss), 2),
            "unit": "sq_meters",
        }

    @staticmethod
    def get_change_statistics_history(
        db: Session,
        project_id: str,
        page: int = 0,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        q = db.query(GrowthHistory).filter(
            GrowthHistory.project_id == project_id,
            GrowthHistory.calculation_type == "change_statistics",
        )
        total = q.count()
        items = q.order_by(GrowthHistory.executed_at.desc()).offset(page * page_size).limit(page_size).all()
        return [h.to_dict() for h in items], total
