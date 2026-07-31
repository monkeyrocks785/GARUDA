"""Measurement service for comparison views."""

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from comparison_engine.config import DEFAULT_MEASUREMENT_UNIT, MEASUREMENT_UNITS
from comparison_engine.database.models import (
    ComparisonMeasurement,
    ComparisonSession,
)


class MeasurementService:
    """Manage measurements on comparison views."""

    @staticmethod
    def create_measurement(
        db: Session,
        session_id: str,
        measurement_type: str,
        value: float,
        geometry: dict[str, Any],
        unit: str = DEFAULT_MEASUREMENT_UNIT,
        label: str | None = None,
        timeline_position: int | None = None,
    ) -> ComparisonMeasurement:
        """Create a new measurement.

        Args:
            db: Database session.
            session_id: Comparison session ID.
            measurement_type: Type of measurement (distance, area, point).
            value: Measured value.
            geometry: Geometry dict with coordinates.
            unit: Measurement unit.
            label: Optional label.
            timeline_position: Timeline position when measured.

        Returns:
            Created ComparisonMeasurement.
        """
        if unit not in MEASUREMENT_UNITS:
            raise ValueError(
                f"Invalid unit: {unit}. Supported: {', '.join(MEASUREMENT_UNITS.keys())}"
            )

        session = db.query(ComparisonSession).get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        measurement = ComparisonMeasurement(
            id=str(uuid.uuid4()),
            session_id=session_id,
            measurement_type=measurement_type,
            unit=unit,
            value=value,
            geometry=json.dumps(geometry),
            label=label,
            timeline_position=timeline_position,
        )
        db.add(measurement)
        db.commit()
        db.refresh(measurement)
        return measurement

    @staticmethod
    def get_measurements(
        db: Session,
        session_id: str,
        measurement_type: str | None = None,
    ) -> list[ComparisonMeasurement]:
        """Get measurements for a session."""
        query = (
            db.query(ComparisonMeasurement)
            .filter(ComparisonMeasurement.session_id == session_id)
        )
        if measurement_type:
            query = query.filter(ComparisonMeasurement.measurement_type == measurement_type)
        return query.order_by(ComparisonMeasurement.created_at).all()

    @staticmethod
    def delete_measurement(
        db: Session,
        measurement_id: str,
        session_id: str,
    ) -> bool:
        """Delete a measurement."""
        measurement = (
            db.query(ComparisonMeasurement)
            .filter(
                ComparisonMeasurement.id == measurement_id,
                ComparisonMeasurement.session_id == session_id,
            )
            .first()
        )
        if measurement is None:
            return False
        db.delete(measurement)
        db.commit()
        return True

    @staticmethod
    def delete_all_measurements(
        db: Session,
        session_id: str,
    ) -> int:
        """Delete all measurements for a session."""
        measurements = (
            db.query(ComparisonMeasurement)
            .filter(ComparisonMeasurement.session_id == session_id)
            .all()
        )
        count = len(measurements)
        for m in measurements:
            db.delete(m)
        db.commit()
        return count

    @staticmethod
    def compute_distance(
        x1: float, y1: float,
        x2: float, y2: float,
        pixel_size: float | None = None,
    ) -> dict[str, Any]:
        """Compute distance between two points.

        Args:
            x1, y1: First point coordinates.
            x2, y2: Second point coordinates.
            pixel_size: Optional pixel size for real-world units.

        Returns:
            Dictionary with distance values in various units.
        """
        dx = x2 - x1
        dy = y2 - y1
        pixel_distance = (dx ** 2 + dy ** 2) ** 0.5

        result = {
            "pixel_distance": pixel_distance,
            "dx": dx,
            "dy": dy,
        }

        if pixel_size is not None:
            result["real_distance"] = pixel_distance * pixel_size
            result["pixel_size"] = pixel_size

        return result

    @staticmethod
    def compute_area(
        coordinates: list[list[float]],
    ) -> dict[str, Any]:
        """Compute area of a polygon using the Shoelace formula.

        Args:
            coordinates: List of [x, y] coordinate pairs.

        Returns:
            Dictionary with area value in square pixels.
        """
        n = len(coordinates)
        if n < 3:
            return {"area": 0.0, "perimeter": 0.0}

        # Shoelace formula
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]
        area = abs(area) / 2.0

        # Perimeter
        perimeter = 0.0
        for i in range(n):
            j = (i + 1) % n
            dx = coordinates[j][0] - coordinates[i][0]
            dy = coordinates[j][1] - coordinates[i][1]
            perimeter += (dx ** 2 + dy ** 2) ** 0.5

        return {
            "area": area,
            "perimeter": perimeter,
            "vertex_count": n,
        }

    @staticmethod
    def to_dict(measurement: ComparisonMeasurement) -> dict[str, Any]:
        """Convert measurement to dictionary."""
        return {
            "id": measurement.id,
            "session_id": measurement.session_id,
            "measurement_type": measurement.measurement_type,
            "unit": measurement.unit,
            "value": measurement.value,
            "geometry": json.loads(measurement.geometry) if measurement.geometry else None,
            "label": measurement.label,
            "timeline_position": measurement.timeline_position,
            "created_at": measurement.created_at.isoformat() if measurement.created_at else None,
        }
