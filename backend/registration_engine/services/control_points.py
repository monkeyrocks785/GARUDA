"""Control point management service."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from registration_engine.database.models import ControlPoint, ImageRegistration


class ControlPointService:
    """Manage control points for manual registration."""

    @staticmethod
    def add_control_point(
        db: Session,
        registration_id: str,
        ref_x: float,
        ref_y: float,
        target_x: float,
        target_y: float,
        ref_lon: float | None = None,
        ref_lat: float | None = None,
        target_lon: float | None = None,
        target_lat: float | None = None,
        label: str | None = None,
        notes: str | None = None,
    ) -> ControlPoint:
        """Add a control point to a registration.

        Args:
            db: Database session.
            registration_id: Registration job ID.
            ref_x: Reference image X pixel coordinate.
            ref_y: Reference image Y pixel coordinate.
            target_x: Target image X pixel coordinate.
            target_y: Target image Y pixel coordinate.
            ref_lon: Reference longitude (optional).
            ref_lat: Reference latitude (optional).
            target_lon: Target longitude (optional).
            target_lat: Target latitude (optional).
            label: Optional label for the point.
            notes: Optional notes.

        Returns:
            Created ControlPoint.

        Raises:
            ValueError: If registration not found or too many points.
        """
        registration = db.query(ImageRegistration).get(registration_id)
        if registration is None:
            raise ValueError(f"Registration not found: {registration_id}")

        # Get current point count
        existing_count = (
            db.query(ControlPoint)
            .filter(ControlPoint.registration_id == registration_id)
            .count()
        )

        from registration_engine.config import MAX_CONTROL_POINTS
        if existing_count >= MAX_CONTROL_POINTS:
            raise ValueError(
                f"Maximum control points ({MAX_CONTROL_POINTS}) reached"
            )

        cp = ControlPoint(
            id=str(uuid.uuid4()),
            registration_id=registration_id,
            point_index=existing_count,
            ref_x=ref_x,
            ref_y=ref_y,
            target_x=target_x,
            target_y=target_y,
            ref_lon=ref_lon,
            ref_lat=ref_lat,
            target_lon=target_lon,
            target_lat=target_lat,
            label=label,
            notes=notes,
        )

        db.add(cp)
        db.commit()
        db.refresh(cp)
        return cp

    @staticmethod
    def add_multiple_control_points(
        db: Session,
        registration_id: str,
        points: list[dict[str, Any]],
    ) -> list[ControlPoint]:
        """Add multiple control points at once.

        Args:
            db: Database session.
            registration_id: Registration job ID.
            points: List of point dictionaries with ref_x, ref_y, target_x, target_y.

        Returns:
            List of created ControlPoints.
        """
        created = []
        for pt in points:
            cp = ControlPointService.add_control_point(
                db=db,
                registration_id=registration_id,
                ref_x=pt["ref_x"],
                ref_y=pt["ref_y"],
                target_x=pt["target_x"],
                target_y=pt["target_y"],
                ref_lon=pt.get("ref_lon"),
                ref_lat=pt.get("ref_lat"),
                target_lon=pt.get("target_lon"),
                target_lat=pt.get("target_lat"),
                label=pt.get("label"),
                notes=pt.get("notes"),
            )
            created.append(cp)
        return created

    @staticmethod
    def move_control_point(
        db: Session,
        point_id: str,
        registration_id: str,
        ref_x: float,
        ref_y: float,
        target_x: float,
        target_y: float,
    ) -> ControlPoint:
        """Move a control point to new coordinates.

        Args:
            db: Database session.
            point_id: Control point ID.
            registration_id: Registration ID (for ownership check).
            ref_x: New reference X coordinate.
            ref_y: New reference Y coordinate.
            target_x: New target X coordinate.
            target_y: New target Y coordinate.

        Returns:
            Updated ControlPoint.

        Raises:
            ValueError: If point not found.
        """
        cp = (
            db.query(ControlPoint)
            .filter(
                ControlPoint.id == point_id,
                ControlPoint.registration_id == registration_id,
            )
            .first()
        )

        if cp is None:
            raise ValueError(f"Control point not found: {point_id}")

        cp.ref_x = ref_x
        cp.ref_y = ref_y
        cp.target_x = target_x
        cp.target_y = target_y
        cp.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(cp)
        return cp

    @staticmethod
    def delete_control_point(
        db: Session,
        point_id: str,
        registration_id: str,
    ) -> bool:
        """Delete a control point.

        Args:
            db: Database session.
            point_id: Control point ID.
            registration_id: Registration ID (for ownership check).

        Returns:
            True if deleted, False if not found.
        """
        cp = (
            db.query(ControlPoint)
            .filter(
                ControlPoint.id == point_id,
                ControlPoint.registration_id == registration_id,
            )
            .first()
        )

        if cp is None:
            return False

        db.delete(cp)

        # Reindex remaining points
        remaining = (
            db.query(ControlPoint)
            .filter(ControlPoint.registration_id == registration_id)
            .order_by(ControlPoint.point_index)
            .all()
        )
        for i, pt in enumerate(remaining):
            pt.point_index = i

        db.commit()
        return True

    @staticmethod
    def delete_all_control_points(
        db: Session,
        registration_id: str,
    ) -> int:
        """Delete all control points for a registration.

        Args:
            db: Database session.
            registration_id: Registration ID.

        Returns:
            Number of points deleted.
        """
        points = (
            db.query(ControlPoint)
            .filter(ControlPoint.registration_id == registration_id)
            .all()
        )
        count = len(points)
        for pt in points:
            db.delete(pt)
        db.commit()
        return count

    @staticmethod
    def get_control_points(
        db: Session,
        registration_id: str,
    ) -> list[ControlPoint]:
        """Get all control points for a registration.

        Args:
            db: Database session.
            registration_id: Registration ID.

        Returns:
            List of ControlPoint objects.
        """
        return (
            db.query(ControlPoint)
            .filter(ControlPoint.registration_id == registration_id)
            .order_by(ControlPoint.point_index)
            .all()
        )

    @staticmethod
    def get_control_point(
        db: Session,
        point_id: str,
        registration_id: str,
    ) -> ControlPoint | None:
        """Get a single control point.

        Args:
            db: Database session.
            point_id: Control point ID.
            registration_id: Registration ID.

        Returns:
            ControlPoint or None.
        """
        return (
            db.query(ControlPoint)
            .filter(
                ControlPoint.id == point_id,
                ControlPoint.registration_id == registration_id,
            )
            .first()
        )

    @staticmethod
    def to_dict(cp: ControlPoint) -> dict[str, Any]:
        """Convert ControlPoint to dictionary.

        Args:
            cp: ControlPoint instance.

        Returns:
            Dictionary representation.
        """
        return {
            "id": cp.id,
            "registration_id": cp.registration_id,
            "point_index": cp.point_index,
            "ref_x": cp.ref_x,
            "ref_y": cp.ref_y,
            "target_x": cp.target_x,
            "target_y": cp.target_y,
            "ref_lon": cp.ref_lon,
            "ref_lat": cp.ref_lat,
            "target_lon": cp.target_lon,
            "target_lat": cp.target_lat,
            "residual": cp.residual,
            "is_inlier": cp.is_inlier,
            "label": cp.label,
            "notes": cp.notes,
            "created_at": cp.created_at.isoformat() if cp.created_at else None,
            "updated_at": cp.updated_at.isoformat() if cp.updated_at else None,
        }
