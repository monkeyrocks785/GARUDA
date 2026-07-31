
from sqlalchemy.orm import Session

from models.health import HealthRecord


class HealthRepository:
    """Repository for health check operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_latest(self, component: str | None = None) -> HealthRecord | None:
        query = self.db.query(HealthRecord).order_by(HealthRecord.created_at.desc())
        if component:
            query = query.filter(HealthRecord.component == component)
        return query.first()

    def create(self, status: str, message: str | None = None, component: str = "system") -> HealthRecord:
        record = HealthRecord(status=status, message=message, component=component)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_all(self, limit: int = 100) -> list[HealthRecord]:
        return self.db.query(HealthRecord).order_by(HealthRecord.created_at.desc()).limit(limit).all()
