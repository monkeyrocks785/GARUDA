"""Rule Evaluation Engine.

Evaluates rule conditions against entities, observations, relationships,
growth metrics, temporal data, and spatial geometry.
Supports AND/OR/NOT logical operators and nested condition groups.
"""

import json
import logging
import math
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from growth_engine.database.models import GrowthMetric
from knowledge_engine.database.models import Entity, EntityObservation, EntityRelationship
from rules_engine.database.models import Rule, RuleAction, RuleCondition

logger = logging.getLogger("garuda.rules.evaluation")


def _parse_value(v: Any) -> Any:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (json.JSONDecodeError, TypeError):
            return v
    return v


def _to_float(v: Any) -> float | None:
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _get_entity_field(entity: Entity, field: str) -> Any:
    field_map = {
        "id": entity.id,
        "entity_type": entity.entity_type,
        "name": entity.name,
        "description": entity.description,
        "status": entity.status,
        "confidence": entity.confidence,
        "observation_count": entity.observation_count,
        "first_observed_at": entity.first_observed_at,
        "last_observed_at": entity.last_observed_at,
        "favorite": entity.favorite,
        "archived": entity.archived,
        "created_at": entity.created_at,
        "modified_at": entity.modified_at,
    }
    if field in field_map:
        return field_map[field]
    if field in ("geometry_json", "attributes_json", "tags_json"):
        return getattr(entity, field, None)
    if field.startswith("attributes."):
        attr_key = field[len("attributes."):]
        attrs = _parse_value(entity.attributes_json) or {}
        return attrs.get(attr_key)
    if field.startswith("tags."):
        tag_key = field[len("tags."):]
        tags = _parse_value(entity.tags_json) or []
        return tag_key in tags
    return _parse_value(entity.attributes_json) if entity.attributes_json else None


def _evaluate_comparison(actual: Any, operator: str, expected: Any) -> bool:
    if actual is None:
        return False
    if operator == "equals":
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.lower() == expected.lower()
        return actual == expected
    if operator == "not_equals":
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.lower() != expected.lower()
        return actual != expected
    if operator in ("greater_than", "gt"):
        a = _to_float(actual)
        e = _to_float(expected)
        return a is not None and e is not None and a > e
    if operator in ("less_than", "lt"):
        a = _to_float(actual)
        e = _to_float(expected)
        return a is not None and e is not None and a < e
    if operator == "between":
        if isinstance(expected, list) and len(expected) == 2:
            a = _to_float(actual)
            e0 = _to_float(expected[0])
            e1 = _to_float(expected[1])
            return a is not None and e0 is not None and e1 is not None and e0 <= a <= e1
        return False
    if operator == "contains":
        if isinstance(actual, str) and isinstance(expected, str):
            return expected.lower() in actual.lower()
        if isinstance(actual, (list, tuple)):
            return expected in actual
        return False
    if operator == "starts_with":
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.lower().startswith(expected.lower())
        return False
    if operator == "ends_with":
        if isinstance(actual, str) and isinstance(expected, str):
            return actual.lower().endswith(expected.lower())
        return False
    return False


def _evaluate_spatial_condition(entity: Entity, condition: RuleCondition) -> bool:
    ct = condition.condition_type
    expected = _parse_value(condition.value_json)

    if ct in ("inside_aoi", "within_distance", "intersects", "touches"):
        if not entity.geometry_json:
            return False
        try:
            entity_geo = json.loads(entity.geometry_json)
        except (json.JSONDecodeError, TypeError):
            return False

        import_geo = None
        if isinstance(expected, dict):
            import_geo = expected
        elif isinstance(expected, str):
            try:
                import_geo = json.loads(expected)
            except (json.JSONDecodeError, TypeError):
                return False

        if not import_geo or not isinstance(import_geo, dict):
            return False

        if ct == "inside_aoi":
            return _check_inside_aoi(entity_geo, import_geo)
        if ct == "within_distance":
            dist = float(condition.field)
            return _check_within_distance(entity_geo, import_geo, dist)
        if ct == "intersects":
            return _check_intersects(entity_geo, import_geo)
        if ct == "touches":
            return _check_touches(entity_geo, import_geo)
    return False


def _check_inside_aoi(entity_geo: dict, aoi_geo: dict) -> bool:
    if entity_geo.get("type") == "Point":
        coords = entity_geo.get("coordinates")
        if coords and aoi_geo.get("type") == "Polygon":
            return _point_in_polygon(coords, aoi_geo.get("coordinates", [[]])[0])
    return False


def _point_in_polygon(point: list[float], polygon: list[list[float]]) -> bool:
    x, y = point[0], point[1]
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i][0], polygon[i][1]
        xj, yj = polygon[j][0], polygon[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _check_within_distance(entity_geo: dict, target_geo: dict, max_dist: float) -> bool:
    def _get_centroid(g):
        if g.get("type") == "Point":
            return g["coordinates"]
        coords = g.get("coordinates", [])
        if g.get("type") == "Polygon":
            c = [sum(p[0] for p in coords[0]) / len(coords[0]), sum(p[1] for p in coords[0]) / len(coords[0])]
            return c
        return None

    ec = _get_centroid(entity_geo)
    tc = _get_centroid(target_geo)
    if ec and tc:
        d = math.sqrt((ec[0] - tc[0]) ** 2 + (ec[1] - tc[1]) ** 2)
        return d <= max_dist
    return False


def _check_intersects(entity_geo: dict, target_geo: dict) -> bool:
    return entity_geo.get("type") == target_geo.get("type")


def _check_touches(entity_geo: dict, target_geo: dict) -> bool:
    return False


def _evaluate_temporal_condition(db: Session, entity: Entity, condition: RuleCondition) -> bool:
    ct = condition.condition_type
    expected = _parse_value(condition.value_json)

    if ct == "first_observed":
        if not entity.first_observed_at:
            return False
        if condition.operator == "before":
            return entity.first_observed_at < _parse_datetime(expected)
        if condition.operator == "after":
            return entity.first_observed_at > _parse_datetime(expected)
        return entity.first_observed_at is not None

    if ct == "last_observed":
        if not entity.last_observed_at:
            return False
        if condition.operator == "before":
            return entity.last_observed_at < _parse_datetime(expected)
        if condition.operator == "after":
            return entity.last_observed_at > _parse_datetime(expected)
        return entity.last_observed_at is not None

    if ct == "observation_count":
        count = entity.observation_count or 0
        e = _to_float(expected) or 0
        if condition.operator in ("greater_than", "gt"):
            return count > e
        if condition.operator in ("less_than", "lt"):
            return count < e
        if condition.operator == "equals":
            return count == e
        if condition.operator == "between" and isinstance(expected, list):
            return expected[0] <= count <= expected[1]
        return count >= e

    return False


def _parse_datetime(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                continue
    return datetime.now(timezone.utc)


def _evaluate_growth_condition(db: Session, entity: Entity, condition: RuleCondition) -> bool:
    ct = condition.condition_type
    expected = _parse_value(condition.value_json)

    if ct in ("growth_rate", "forecast_value", "confidence_score"):
        metric_name = condition.field
        gm = (
            db.query(GrowthMetric)
            .filter(
                GrowthMetric.entity_id == entity.id,
                GrowthMetric.metric_name == metric_name,
            )
            .order_by(GrowthMetric.computed_at.desc())
            .first()
        )
        if gm is None:
            return False

        value = gm.metric_value
        e = _to_float(expected) or 0
        if condition.operator in ("greater_than", "gt"):
            return value > e
        if condition.operator in ("less_than", "lt"):
            return value < e
        if condition.operator == "equals":
            return abs(value - e) < 1e-10
        if condition.operator == "between" and isinstance(expected, list):
            return expected[0] <= value <= expected[1]
        return value >= e

    return False


def _evaluate_relationship_condition(db: Session, entity: Entity, condition: RuleCondition) -> bool:
    ct = condition.condition_type
    expected = _parse_value(condition.value_json)

    if ct == "entity":
        rel_type = condition.field
        q = db.query(EntityRelationship).filter(
            (EntityRelationship.source_entity_id == entity.id)
            | (EntityRelationship.target_entity_id == entity.id)
        )
        if rel_type:
            q = q.filter(EntityRelationship.relationship_type == rel_type)

        count = q.count()
        e = _to_float(expected) or 1
        if condition.operator in ("greater_than", "gt"):
            return count > e
        if condition.operator in ("less_than", "lt"):
            return count < e
        return count >= e

    return False


def _evaluate_single_condition(db: Session, entity: Entity, condition: RuleCondition) -> bool:
    ct = condition.condition_type

    spatial_types = {"inside_aoi", "within_distance", "intersects", "touches"}
    temporal_types = {"first_observed", "last_observed", "observation_count"}
    growth_types = {"growth_rate", "forecast_value", "confidence_score"}
    relationship_types = {"entity"}

    if ct in spatial_types:
        return _evaluate_spatial_condition(entity, condition)
    if ct in temporal_types:
        return _evaluate_temporal_condition(db, entity, condition)
    if ct in growth_types:
        return _evaluate_growth_condition(db, entity, condition)
    if ct in relationship_types:
        return _evaluate_relationship_condition(db, entity, condition)

    actual = _get_entity_field(entity, condition.field)
    expected = _parse_value(condition.value_json)
    return _evaluate_comparison(actual, condition.operator, expected)


def _evaluate_condition_group(
    db: Session,
    entity: Entity,
    conditions: list[RuleCondition],
) -> bool:
    if not conditions:
        return True

    result = None
    current_logical = "AND"

    for cond in conditions:
        val = _evaluate_single_condition(db, entity, cond)

        if cond.logical_operator == "NOT":
            val = not val

        if result is None:
            result = val
        elif current_logical == "AND":
            result = result and val
        elif current_logical == "OR":
            result = result or val

        if cond.logical_operator in ("AND", "OR"):
            current_logical = cond.logical_operator

    return result if result is not None else True


class EvaluationService:
    """Evaluates rules against entities and generates alerts."""

    @staticmethod
    def evaluate_rule(db: Session, rule: Rule, entity: Entity) -> dict | None:
        conditions = (
            db.query(RuleCondition)
            .filter(RuleCondition.rule_id == rule.id)
            .order_by(RuleCondition.sort_order.asc())
            .all()
        )

        if not conditions:
            return None

        groups: dict[int, list[RuleCondition]] = {}
        for c in conditions:
            groups.setdefault(c.group_index, []).append(c)

        all_groups_passed = True
        for group_idx in sorted(groups.keys()):
            group_passed = _evaluate_condition_group(db, entity, groups[group_idx])
            if not group_passed:
                all_groups_passed = False
                break

        if not all_groups_passed:
            return None

        detail = {
            "entity_id": entity.id,
            "entity_name": entity.name,
            "entity_type": entity.entity_type,
            "rule_name": rule.name,
            "rule_type": rule.rule_type,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

        return detail

    @staticmethod
    def evaluate_rule_for_project(db: Session, rule: Rule, project_id: str) -> list[dict]:
        alerts_generated = []
        entities = (
            db.query(Entity)
            .filter(
                Entity.project_id == project_id,
                Entity.archived == False,
            )
            .all()
        )

        for entity in entities:
            try:
                result = EvaluationService.evaluate_rule(db, rule, entity)
                if result:
                    alerts_generated.append(result)
            except Exception as e:
                logger.warning(f"Error evaluating rule {rule.id} on entity {entity.id}: {e}")

        return alerts_generated
