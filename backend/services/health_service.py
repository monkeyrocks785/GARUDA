
from sqlalchemy.orm import Session

from repositories.health_repository import HealthRepository


class HealthService:
    """Service for health check operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = HealthRepository(db)

    def check_health(self) -> dict:
        """Perform a health check and return system status."""
        record = self.repository.create(
            status="healthy",
            message="System is operational",
            component="api",
        )
        return {
            "status": "healthy",
            "timestamp": record.created_at.isoformat(),
            "database": "connected",
        }

    def get_system_status(self) -> dict:
        """Get current system status."""
        latest = self.repository.get_latest(component="api")
        return {
            "status": latest.status if latest else "unknown",
            "last_checked": latest.created_at.isoformat() if latest else None,
        }
