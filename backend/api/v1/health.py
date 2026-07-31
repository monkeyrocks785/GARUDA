from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.settings import settings
from database.connection import get_db
from services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: str
    environment: str
    timestamp: str


class DetailedHealthResponse(BaseModel):
    status: str
    database: str
    timestamp: str


_start_time = datetime.now(UTC)


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    uptime = datetime.now(UTC) - _start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        uptime=f"{hours}h {minutes}m {seconds}s",
        environment=settings.APP_ENV,
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(db: Session = Depends(get_db)) -> DetailedHealthResponse:
    """Detailed health check including database status."""
    service = HealthService(db)
    result = service.check_health()

    return DetailedHealthResponse(
        status=result["status"],
        database=result["database"],
        timestamp=result["timestamp"],
    )
